import logging
import os
import sqlite3
import sys
from dataclasses import astuple
from typing import Any, Type

import psycopg

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv
from load_data import (FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork,
                       convert_sqlite_row_to_dataclass)

load_dotenv()


dsl = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

BATCH_SIZE = 100


def test_transfer(
    sqlite_cursor: sqlite3.Cursor,
    pg_cursor: psycopg.Cursor,
    table_name: str,
    dataclass_type: type,
) -> None:
    """Тест для проверки корректности переноса данных из SQLite в PostgreSQL."""
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")

    while batch := sqlite_cursor.fetchmany(BATCH_SIZE):
        original_batch = [
            convert_sqlite_row_to_dataclass(row, dataclass_type) for row in batch
        ]

        ids = [getattr(obj, "id") for obj in original_batch]

        pg_cursor.execute(
            f"SELECT * FROM content.{table_name} WHERE id = ANY(%s)", [ids]
        )

        transferred_batch = []
        for row in pg_cursor.fetchall():
            row_dict = dict(zip([desc.name for desc in pg_cursor.description], row))
            transferred_batch.append(dataclass_type(**row_dict))

        original_batch_sorted = sorted(original_batch, key=lambda x: x.id)
        transferred_batch_sorted = sorted(transferred_batch, key=lambda x: x.id)

        assert len(original_batch) == len(
            transferred_batch
        ), f"Количество записей не совпадает для {table_name}"

        for original, transferred in zip(
            original_batch_sorted, transferred_batch_sorted
        ):
            assert (
                original == transferred
            ), f"Содержимое записей не совпадает для {table_name}. ORIGINAL {original} \n TRANSFERED \n {transferred}\n "


def run_all_tests():
    with sqlite3.connect("db.sqlite") as sqlite_conn, psycopg.connect(**dsl) as pg_conn:
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()

        tables_to_test = [
            ("genre", Genre),
            ("person", Person),
            ("film_work", FilmWork),
            ("genre_film_work", GenreFilmWork),
            ("person_film_work", PersonFilmWork),
        ]

        for table_name, dataclass_type in tables_to_test:
            print(f"Тестирование таблицы {table_name}...")
            test_transfer(sqlite_cursor, pg_cursor, table_name, dataclass_type)
            print(f" Таблица {table_name} проверена успешно!")

        sqlite_cursor.close()
        pg_cursor.close()


if __name__ == "__main__":
    run_all_tests()
