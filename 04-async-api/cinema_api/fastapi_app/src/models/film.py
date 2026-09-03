from enum import Enum
from typing import List, Optional

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
    genres: List[Genre]
    title: str
    description: Optional[str] = None
    directors: List[Person]
    genres_names: List[str]
    actors_names: List[str]
    directors_names: List[str]
    writers_names: List[str]
    actors: List[Person]
    writers: List[Person]

