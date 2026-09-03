from pydantic import BaseModel, Field
from typing import Optional

class Genre(BaseModel):
    uuid: str
    name: str


class Person(BaseModel):
    uuid: str
    full_name: str


class Film(BaseModel):
    uuid: str = Field(..., alias="id")
    title: str
    imdb_rating: Optional[float] = None
    description: Optional[str] = None
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmShort(BaseModel):
    uuid: str = Field(..., alias="id")
    title: str
    imdb_rating: Optional[float] = None

