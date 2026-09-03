from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TableConfig(BaseModel):
    name: str
    query: str


class PersonModel(BaseModel):
    id: str
    name: str


class FilmElasticsearchModel(BaseModel):
    id: str
    imdb_rating: Optional[float] = None
    genres: List[str]
    title: str
    description: Optional[str] = None
    directors: List[PersonModel]
    actors_names: List[str]
    directors_names: List[str]
    writers_names: List[str]
    actors: List[PersonModel]
    writers: List[PersonModel]
