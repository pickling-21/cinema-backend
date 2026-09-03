import logging
import os
import sqlite3
from contextlib import closing
from dataclasses import astuple
from typing import Any, Generator, Type

import psycopg
from dotenv import load_dotenv
from src.models import (FIELD_MAPPING, BaseMoviesDataClass, FilmWork, Genre,
                        GenreFilmWork, Person, PersonFilmWork)

load_dotenv()

dsl = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

BATCH_SIZE = 100

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_sqlite_row_to_dataclass(
    row: sqlite3.Row, dataclass_type: Type[BaseMoviesDataClass]
) -> BaseMoviesDataClass:
    """Преобразует строку SQLite в датакласс с учетом маппинга полей"""
    table_name = dataclass_type.get_table_name()
    field_mapping = FIELD_MAPPING.get(table_name, {})

    mapped_data = {}
    for sqlite_field, dataclass_field in field_mapping.items():
        if sqlite_field in row.keys():
            mapped_data[dataclass_field] = row[sqlite_field]

    result = dataclass_type(**mapped_data)
    return result


def transform_sqlite_data(
    sqlite_cursor: sqlite3.Cursor, table_name: str, obj_type: Type[BaseMoviesDataClass]
) -> Generator[list[Type[Any]], None, None]:
    """Преобразует данные из SQLite в объекты датаклассов"""
    for batch in extract_data(sqlite_cursor, table_name, obj_type):
        yield [convert_sqlite_row_to_dataclass(row, obj_type) for row in batch]


def extract_data(
    sqlite_cursor: sqlite3.Cursor, table_name: str, obj_type: Type[BaseMoviesDataClass]
) -> Generator[list[sqlite3.Row], None, None]:
    """Извлекает данные из SQLite пачками"""
    try:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        while results := sqlite_cursor.fetchmany(BATCH_SIZE):
            yield results
    except sqlite3.Error as e:
        logger.error(f"Error extracting from {table_name}: {e}")
        raise


def generate_insert_query(dataclass_type: Type[BaseMoviesDataClass]) -> str:
    """Генерирует SQL запрос для вставки на основе датакласса"""
    table_name = dataclass_type.get_table_name()
    fields = dataclass_type.get_fields()

    columns = ", ".join(fields)
    placeholders = ", ".join(["%s"] * len(fields))

    return f"""
        INSERT INTO content.{table_name} 
        ({columns}) 
        VALUES ({placeholders})
        ON CONFLICT (id) DO NOTHING
    """


def load_from_sqlite(
    sqlite_cursor: sqlite3.Cursor,
    pg_cursor: psycopg.Cursor,
    table_name: str,
    dataclass_type: Type[BaseMoviesDataClass],
) -> None:
    """Основной метод загрузки данных из SQLite в Postgres"""
    query = generate_insert_query(dataclass_type)
    for batch in transform_sqlite_data(sqlite_cursor, table_name, dataclass_type):
        try:
            batch_as_tuples = [astuple(item) for item in batch]
            pg_cursor.executemany(query, batch_as_tuples)
            logger.info(f"Loaded {len(batch)} records to {table_name}")
        except psycopg.Error as e:
            logger.error(f"Error loading {table_name} batch: {e}")
            raise


def main():
    """Основная функция миграции данных"""
    try:
        with (
            closing(sqlite3.connect("db.sqlite")) as sqlite_conn,
            closing(psycopg.connect(**dsl)) as pg_conn,
        ):
            sqlite_conn.row_factory = sqlite3.Row
            with (
                closing(sqlite_conn.cursor()) as sqlite_cur,
                closing(pg_conn.cursor()) as pg_cur,
            ):
                load_from_sqlite(sqlite_cur, pg_cur, "genre", Genre)
                load_from_sqlite(sqlite_cur, pg_cur, "person", Person)
                load_from_sqlite(sqlite_cur, pg_cur, "film_work", FilmWork)
                load_from_sqlite(sqlite_cur, pg_cur, "genre_film_work", GenreFilmWork)
                load_from_sqlite(sqlite_cur, pg_cur, "person_film_work", PersonFilmWork)

                pg_conn.commit()

                logger.info("Data migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
    print("🎉 Данные успешно перенесены !!!")
