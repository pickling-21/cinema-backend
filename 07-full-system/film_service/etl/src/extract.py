from typing import Any, Iterator

from loguru import logger
from models import TableConfig

DataChunk = list[dict[str, Any]]


class PostgresDataExtractor:
    def __init__(self, postgres_connection, chunk_size: int):
        self.postgres_connection = postgres_connection
        self.chunk_size = chunk_size

    def extract_data(
        self, last_modified: str, table_config: TableConfig
    ) -> Iterator[tuple[list[str], DataChunk]]:
        logger.debug(f"Начали извлечение {last_modified}")
        with self.postgres_connection.cursor() as cursor:
            formatted_query = table_config.query.format(modified=last_modified)
            cursor.execute(formatted_query)

            column_names = [column[0] for column in cursor.description]

            while True:
                data_chunk = cursor.fetchmany(size=self.chunk_size)
                if not data_chunk:
                    break

                logger.debug(
                    f"Extracted {len(data_chunk)} records from {table_config.name}"
                )
                yield column_names, data_chunk
