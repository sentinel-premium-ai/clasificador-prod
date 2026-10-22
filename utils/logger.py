import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logging(log_path="logs"):
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) 
    
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG) 
    logger.addHandler(console_handler)    
    
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_path, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) 
    logger.addHandler(file_handler)
    
    return logger