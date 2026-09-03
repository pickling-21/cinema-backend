from pydantic import Field
from pydantic_settings import BaseSettings
from functional.testdata.es_mapping import schema


class TestSettings(BaseSettings):

    es_host: str = Field('http://elasticsearch:9200')
    es_index: str = "movies"
    es_id_field: str = "id"
    es_index_mapping: dict = schema

    redis_host: str = Field('redis')
    redis_port: str = Field('6379')
    service_url: str = Field('http://fastapi:8000')

test_settings = TestSettings()