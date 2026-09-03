import logging
import time
from contextlib import closing

import backoff
import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from extract import PostgresDataExtractor
from load import ElasticsearchDataLoader
from loguru import logger
from models import TableConfig
from psycopg2.errors import ConnectionException, OperationalError
from psycopg2.extras import DictCursor
from queries import FILM_WORK_QUERY
from settings import settings
from storage import JsonFileStorage, StateManager
from transform import DataTransformer

logging.basicConfig(level=logging.INFO)
logger.add("etl.log", rotation="10 MB")

table_configurations = [
    TableConfig(
        name="film_work",
        query=FILM_WORK_QUERY.format(table="fw")
        + " WHERE fw.modified > '{modified}' GROUP BY fw.id ORDER BY fw.modified",
    ),
    TableConfig(
        name="person",
        query=FILM_WORK_QUERY.format(table="p")
        + " WHERE p.modified > '{modified}' GROUP BY p.id, fw.id ORDER BY p.modified",
    ),
    TableConfig(
        name="genre",
        query=FILM_WORK_QUERY.format(table="g")
        + " WHERE g.modified > '{modified}' GROUP BY g.id, fw.id ORDER BY g.modified",
    ),
]


@backoff.on_exception(
    backoff.expo,
    (ElasticConnectionError, ConnectionException, OperationalError),
    max_time=120,
)
def execute_etl_pipeline(state_manager: StateManager):
    postgres_config = {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "dbname": settings.postgres_db,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
    }

    with (
        closing(
            psycopg2.connect(**postgres_config, cursor_factory=DictCursor)
        ) as postgres_connection,
        closing(Elasticsearch(settings.elasticsearch_url)) as elasticsearch_connection,
    ):
        data_transformer = DataTransformer()
        loader = ElasticsearchDataLoader(elasticsearch_connection)
        extractor = PostgresDataExtractor(postgres_connection, settings.chunk_size)

        for table_config in table_configurations:
            t_name = table_config.name
            logger.info(f"Процесс {t_name}")

            max_modified_for_table = None
            has_processed_data = False

            for column_names, data_chunk in extractor.extract_data(
                state_manager.get_state(t_name), table_config
            ):
                if not data_chunk:
                    continue
                transformed_data, max_modified = data_transformer.transform_batch(
                    data_chunk
                )
                loader.load_data_batch(transformed_data)
                state_manager.set_state(t_name, max_modified.isoformat())


if __name__ == "__main__":
    state_manager = StateManager(JsonFileStorage(file_path=settings.state_file))
    logger.info("Работаем")

    while True:
        try:
            logger.info("Начало итерации")
            execute_etl_pipeline(state_manager)
        except Exception as error:
            logger.error(f"Ошибка{error}")

        logger.info(f"Спим {settings.sleep_timeout} сек.")
        time.sleep(settings.sleep_timeout)
