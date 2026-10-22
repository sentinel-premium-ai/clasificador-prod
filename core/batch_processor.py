from datetime import datetime, timedelta
from typing import Optional
from core.api_client import ApiClient
from core.image_processor import ImageProcessor
import logging

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, oracle_client: ApiClient, image_processor: ImageProcessor):
        self.oracle_client = oracle_client
        self.image_processor = image_processor

    def process_date(self, process_date: datetime) -> None:
        images = self.oracle_client.fetch_image_paths(process_date)
        if not images:
            return

        date_str = process_date.strftime('%Y-%m-%d')
        processed = self.image_processor.postgres_client.get_processed_filenames(date_str)

        if processed:
            original_count = len(images)
            images = [img for img in images if img.path not in processed]
            skipped = original_count - len(images)
            logger.info(f"Skipping {skipped} already-processed images for {date_str}. Remaining: {len(images)}.")

        if images:
            self.image_processor.process_batch(images)
        else:
            logger.info(f"All images for {date_str} already processed. Nothing to do.")

    def process_date_range(self, start_date: datetime, end_date: Optional[datetime] = None) -> None:
        current_date = start_date
        while current_date <= (end_date or start_date):
            print(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
            self.process_date(current_date)
            if end_date is None:
                break
            current_date += timedelta(days=1)