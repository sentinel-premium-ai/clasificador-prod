import os
import tempfile
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
from core.api_client import ImagePath
from db.postgres_client import PostgresClient
from core.model_handler import ModelHandler

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, postgres_client: PostgresClient, model_handler: ModelHandler, config: Dict):
        self.postgres_client = postgres_client
        self.model_handler = model_handler
        self.config = config
        self.photos_base_url = str(config.get('photos_base_url', '')).rstrip('/')

    def get_history_path(self, filename: str) -> str:
        return f"fake/history/path/{filename}"

    def _build_image_url(self, image: ImagePath) -> str:
        return f"{self.photos_base_url}/{image.nro_smf}/{image.path}"

    def _classify_single(self, image: ImagePath) -> Dict:
        """Downloads and classifies a single image, returns result dict."""
        image_url = self._build_image_url(image)
        tmp_path = None

        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 404:
                logger.warning(f"Image not found (404): {image_url}")
                class_id = 3
                confidence = 0.0
            else:
                response.raise_for_status()
                suffix = Path(image.path).suffix or '.jpg'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                class_id, confidence = self.model_handler.classify_image(tmp_path)
        except requests.RequestException as e:
            logger.error(f"Request error for {image_url}: {e}")
            class_id = 3
            confidence = 0.0
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        history_path = self.get_history_path(os.path.basename(image.path))
        return {
            'image_data': image,
            'class_id': class_id,
            'confidence': confidence,
            'full_path': image_url,
            'history_path': history_path,
        }

    def process_image(self, image: ImagePath) -> None:
        """Classifies a single image and inserts it immediately (legacy, kept for compatibility)."""
        result = self._classify_single(image)
        self.postgres_client.insert_classification(
            image_data=result['image_data'],
            class_id=result['class_id'],
            confidence=result['confidence'],
            full_path=result['full_path'],
            history_path=result['history_path'],
        )

    def process_batch(self, images: List[ImagePath], batch_size: int = 500) -> None:
        total = len(images)
        buffer = []

        for i, image in enumerate(images, 1):
            try:
                result = self._classify_single(image)
                buffer.append(result)
            except Exception as e:
                logger.error(f"Error classifying image {image.path}: {e}")

            if len(buffer) >= batch_size:
                try:
                    self.postgres_client.batch_insert_classifications(buffer)
                except Exception as e:
                    logger.error(f"Batch insert failed at image {i}/{total}: {e}")
                buffer = []
                logger.info(f"Progress: {i}/{total} images processed and inserted.")

            elif i % 100 == 0:
                logger.info(f"Progress: {i}/{total} images classified (buffer: {len(buffer)}).")

        if buffer:
            try:
                self.postgres_client.batch_insert_classifications(buffer)
                logger.info(f"Final batch inserted: {len(buffer)} records. Total processed: {total}.")
            except Exception as e:
                logger.error(f"Final batch insert failed: {e}")