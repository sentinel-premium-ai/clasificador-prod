from typing import Dict, List
import psycopg2
from psycopg2 import extras
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
                conn = psycopg2.connect(
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
                logger.debug(
                    f"Connected to PostgreSQL: host={self.config['host']} "
                    f"db={self.config['database']} user={self.config['user']}"
                )
                return conn
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
        insert_path_query = """
            INSERT INTO neuralsmf.images_paths_aux(
                path,
                date
            )
            VALUES (%s,%s)
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
                        
                        cursor.execute(insert_path_query, (
                            full_path,
                            image_data.capture_date
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

    def batch_insert_classifications(self, records: List[Dict]):
        """Inserts a list of classification results in a single transaction."""
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
            VALUES %s
        """
        insert_path_query = """
            INSERT INTO neuralsmf.images_paths_aux(path, date)
            VALUES %s
        """

        class_rows = [
            (
                r['class_id'],
                r['full_path'],
                r['image_data'].cod_unicom,
                r['image_data'].ruta,
                r['image_data'].nis_rad,
                r['image_data'].num_itin,
                r['image_data'].capture_date,
                r['image_data'].path,
                f"{r['confidence']:.2f}",
                r['history_path'],
            )
            for r in records
        ]

        path_rows = [
            (r['full_path'], r['image_data'].capture_date)
            for r in records
        ]

        retries = 0
        while retries < self.max_retries:
            try:
                conn = self.get_connection()
                try:
                    with conn.cursor() as cursor:
                        extras.execute_values(
                            cursor, insert_query, class_rows,
                            template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,current_timestamp,null,current_user,null)"
                        )
                        rows_affected = cursor.rowcount
                    conn.commit()
                    logger.info(f"image_classification: {rows_affected} rows committed (batch size={len(records)}).")
                    break
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.close()
            except Exception as e:
                retries += 1
                if retries < self.max_retries:
                    logger.warning(f"Batch insert attempt {retries} failed: {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Batch insert failed after {self.max_retries} attempts: {e}")
                    raise e

        try:
            conn = self.get_connection()
            try:
                with conn.cursor() as cursor:
                    extras.execute_values(cursor, insert_path_query, path_rows)
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"images_paths_aux: {rows_affected} rows committed.")
            except Exception as e:
                conn.rollback()
                logger.warning(f"images_paths_aux insert failed (non-critical): {e}")
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"images_paths_aux connection failed (non-critical): {e}")

    def get_processed_filenames(self, date: str) -> set:
        """Returns the set of file_name values already processed for a given date (YYYY-MM-DD)."""
        query = """
            SELECT file_name FROM neuralsmf.image_classification
            WHERE reading_date = %s
        """
        try:
            conn = self.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (date,))
                    rows = cursor.fetchall()
                result = {row[0] for row in rows}
                logger.info(f"Found {len(result)} already-processed records for date {date}.")
                return result
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch processed filenames for {date}: {e}. Will process all images.")
            return set()