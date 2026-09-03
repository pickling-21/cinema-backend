from datetime import datetime
from typing import Any

from loguru import logger
from models import FilmElasticsearchModel


class DataTransformer:
    def transform_batch(
        self, postgres_data: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], datetime]:
        transformed_records = []
        max_modified_timestamp = None

        for row in postgres_data:
            film_data = FilmElasticsearchModel(**row)
            transformed_record = film_data.model_dump()
            transformed_records.append(transformed_record)

            current_modified = row[-1]
            if (
                max_modified_timestamp is None
                or current_modified > max_modified_timestamp
            ):
                max_modified_timestamp = current_modified

        logger.debug(f"Сделано {len(transformed_records)}")
        return transformed_records, max_modified_timestamp
