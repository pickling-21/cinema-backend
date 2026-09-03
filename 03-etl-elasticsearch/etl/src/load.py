import json
from pathlib import Path

import backoff
from elasticsearch import ConnectionError, Elasticsearch, helpers
from loguru import logger


class ElasticsearchDataLoader:
    INDEX_NAME = "movies"
    ES_SCHEMA_PATH = Path("es_schema.json")

    def __init__(self, es_connection: Elasticsearch):
        self.es_conn = es_connection
        self.create_index()

    def create_index(self) -> None:
        if self.es_conn.indices.exists(index=self.INDEX_NAME):
            logger.info(f"Уже создан {self.INDEX_NAME}")
            return

        with open(self.ES_SCHEMA_PATH) as file:
            elastic_schema = json.load(file)
            self.es_conn.indices.create(index=self.INDEX_NAME, body=elastic_schema)

        logger.info(f"Индекс {self.INDEX_NAME} создан.")

    @backoff.on_exception(backoff.expo, ConnectionError, max_time=120)
    def load_data_batch(self, data_batch):
        actions = (
            {
                "_id": record["id"],
                "_source": record,
            }
            for record in data_batch
        )

        helpers.bulk(client=self.es_conn, index=self.INDEX_NAME, actions=actions)

        logger.info(f"Загружено {len(data_batch)}")
