import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import time

# Re-defining ImagePath here to decouple from db/oracle_client
@dataclass
class ImagePath:
    nro_smf: str
    path: str
    capture_date: datetime
    cod_unicom: str
    nis_rad: str
    ruta: str
    tip_foto: str
    num_itin: str

class ApiClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({"X-API-KEY": self.api_key})

    def fetch_image_paths(self, process_date: datetime) -> List[ImagePath]:
        """
        Fetches all pending images for a given date, handling pagination automatically.
        """
        date_str = process_date.strftime('%Y-%m-%d')
        all_images = []
        page = 1
        page_size = 1000
        has_more = True
        
        self.logger.info(f"Fetching images from API for date: {date_str}")

        while has_more:
            try:
                response = self.session.get(
                    f"{self.base_url}/images/pending",
                    params={"date": date_str, "page": page, "page_size": page_size},
                    timeout=30 
                )
                response.raise_for_status()
                data = response.json()
                
                items = data.get("data", [])
                if not items:
                    break
                
                for item in items:
                    # Parse date string back to datetime object
                    # API returns ISO format usually, let's assume standard format
                    try:
                        cap_date = datetime.fromisoformat(item["capture_date"])
                    except ValueError:
                         # Fallback if format is different
                         cap_date = datetime.strptime(item["capture_date"], "%Y-%m-%dT%H:%M:%S")

                    all_images.append(ImagePath(
                        nro_smf=item["nro_smf"],
                        path=item["path"],
                        capture_date=cap_date,
                        cod_unicom=item["cod_unicom"],
                        nis_rad=item["nis_rad"],
                        ruta=item["ruta"],
                        tip_foto=item["tip_foto"],
                        num_itin=item["num_itin"]
                    ))
                
                has_more = data.get("has_more", False)
                if has_more:
                    page += 1
                    # Small sleep to be nice to the API/Network
                    time.sleep(0.1) 
                    
            except requests.RequestException as e:
                self.logger.error(f"Error fetching page {page} from API: {str(e)}")
                # Decide: retry or fail? For batch process, maybe fail is better than partial data
                # But we could implement simple retry logic here
                raise e

        self.logger.info(f"Total images fetched from API: {len(all_images)}")
        return all_images
