import os
from logging import config as logging_config

from pydantic_settings import BaseSettings

from src.core.logger import LOGGING

logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):    
    PROJECT_NAME: str = "movies"
    
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    
    ELASTIC_HOST: str = "127.0.0.1"
    ELASTIC_PORT: int = 9200
    ELASTIC_SCHEME: str = "http"

    JWT_SECRET_KEY: str = "secret"
    
    @property
    def BASE_DIR(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


settings = Settings()