import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "movies"
    postgres_user: str = "app"
    postgres_password: str = "password"

    elastic_host: str = "localhost"
    elastic_port: int = 9200
    elastic_index: str = "movies"

    chunk_size: int = 100
    sleep_timeout: float = 10.0
    state_file: str = "state.json"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def elasticsearch_url(self) -> str:
        return f"http://{self.elastic_host}:{self.elastic_port}"


settings = Settings()
