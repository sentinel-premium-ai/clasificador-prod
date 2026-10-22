from typing import Dict
import psycopg2
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class PostgresClient:
    def __init__(self, config: Dict):
        self.config = config
        self.max_retries = 3
        self.retry_delay = 2  

    def get_connection(self):
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                return psycopg2.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['user'],
                    password=self.config['password'],                    
                    connect_timeout=10,                    
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
            except psycopg2.Error as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Connection attempt {retries} failed. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                
        logger.error(f"Failed to connect to PostgreSQL after {self.max_retries} attempts")
        raise last_error

    def insert_classification(self, image_data: Dict, class_id: int, confidence: float, 
                            full_path: str, history_path: str):
        insert_query = """
            INSERT INTO neuralsmf.image_classification 
            (
                id_type, 
                isgl_path,
                codunicom,
                ruta,
                nis_rad,           
                itinerary, 
                reading_date, 
                file_name, 
                accuracy_meter_present,
                history_path, 
                created_at, 
                modified_at, 
                created_by, 
                modified_by
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,current_timestamp,null,current_user,null)
        """
        
        retries = 0
        while retries < self.max_retries:
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(insert_query, (
                            class_id,
                            full_path,
                            image_data.cod_unicom,
                            image_data.ruta,
                            image_data.nis_rad,
                            image_data.num_itin,
                            image_data.capture_date,
                            image_data.path,
                            f"{confidence:.2f}",
                            history_path
                        ))
                    conn.commit()
                    return
            except psycopg2.Error as e:
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Insert attempt {retries} failed. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to insert after {self.max_retries} attempts")
                    raise e