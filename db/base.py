import configparser
from abc import ABC, abstractmethod

class DatabaseClient(ABC):
    def __init__(self):
        self.config = self._load_config()
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def disconnect(self):
        pass
    
    def _load_config(self):
        config = configparser.ConfigParser()
        config.read("config/env.ini")
        return config