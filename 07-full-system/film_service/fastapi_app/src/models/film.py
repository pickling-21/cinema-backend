from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Genre(BaseModel):
    id: str
    name: str


class Person(BaseModel):
    id: str
    name: str


class FilmModel(BaseModel):
    id: str
    imdb_rating: Optional[float] = None
    genres: list[Genre]
    title: str
    description: Optional[str] = None
    directors: list[Person]
    genres_names: list[str]
    actors_names: list[str]
    directors_names: list[str]
    writers_names: list[str]
    actors: list[Person]
    writers: list[Person]
