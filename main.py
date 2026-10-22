import argparse
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
import configparser
import os
import logging

from core.api_client import ApiClient
from db.postgres_client import PostgresClient 
from core.model_handler import ModelHandler
from core.image_processor import ImageProcessor
from core.batch_processor import BatchProcessor

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_config():
    config = configparser.ConfigParser()
    config.read('config/env.ini')
    
    # Override with Environment Variables if present (Best Practice for Docker/EC2)
    # Postgres
    if os.environ.get('POSTGRES_DB_HOST'): config['postgres']['db_host'] = os.environ['POSTGRES_DB_HOST']
    if os.environ.get('POSTGRES_DB_NAME'): config['postgres']['db_name'] = os.environ['POSTGRES_DB_NAME']
    if os.environ.get('POSTGRES_DB_USER'): config['postgres']['db_user'] = os.environ['POSTGRES_DB_USER']
    if os.environ.get('POSTGRES_DB_PASS'): config['postgres']['db_pass'] = os.environ['POSTGRES_DB_PASS']
    if os.environ.get('POSTGRES_DB_PORT'): config['postgres']['db_port'] = os.environ['POSTGRES_DB_PORT']

    # Oracle API Config
    # We no longer read Oracle DB config from env vars or ini for the client
    # instead we look for API configuration
    config['api'] = {}
    config['api']['url'] = os.environ.get('ORACLE_API_URL', 'http://localhost:8000')
    config['api']['key'] = os.environ.get('ORACLE_API_KEY', '')
    
    # Model variables (optional)
    if os.environ.get('MODEL_PATH'): config['model']['path'] = os.environ['MODEL_PATH']

    # Photos HTTP server base URL
    if 'paths' not in config:
        config['paths'] = {}
    if os.environ.get('PHOTOS_BASE_URL'):
        config['paths']['photos_base_url'] = os.environ['PHOTOS_BASE_URL']

    return config

def main():
    parser = argparse.ArgumentParser(description='Process and classify images')
    parser.add_argument('--days-back', type=int, help='Number of days to process backwards from today')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD or YYMMDD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD or YYMMDD)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    
    logger = setup_logging(args.debug)
    
    try:        
        config = load_config()
        logger.debug("Configuration loaded successfully")
                
        logger.debug("Initializing components...")
        
        # Initialize API Client instead of Oracle DB Client
        api_url = config['api']['url']
        api_key = config['api']['key']
        
        if not api_key:
             logger.warning("No ORACLE_API_KEY provided. API calls might fail if auth is enabled.")

        oracle_client = ApiClient(base_url=api_url, api_key=api_key)
        logger.debug(f"Oracle API client initialized at {api_url}")
        
        postgres_client = PostgresClient(config['postgres'])
        logger.debug("PostgreSQL client initialized")
        
        model_handler = ModelHandler(
            model_path=config['model']['path'],
            input_shape=tuple(map(int, config['model']['input_shape'].split(',')))
        )
        logger.debug("Model handler initialized")
        
        image_processor = ImageProcessor(postgres_client, model_handler, config['paths'])
        logger.debug("Image processor initialized")
        
        batch_processor = BatchProcessor(oracle_client, image_processor)
        logger.debug("Batch processor initialized")
                
        if args.days_back is not None:
            start_date = datetime.now() - timedelta(days=args.days_back)
            end_date = datetime.now()
        elif args.start_date:
            start_date = parse_date(args.start_date)
            end_date = parse_date(args.end_date) if args.end_date else None
        else:
            start_date = datetime.now()
            end_date = None
        
        logger.info(f"Processing dates from {start_date} to {end_date or 'today'}")
                
        batch_processor.process_date_range(start_date, end_date)
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()