from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from src.models.film import FilmModel
from pydantic import BaseModel

from src.services.film import FilmService, get_film_service


from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


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
    uuid: str =Field(..., alias="id") 
    title: str
    imdb_rating: Optional[float] = None


router = APIRouter()


def _transform_to_film_response(film_model: FilmModel) -> Film:
    genres = [Genre(uuid=g.id, name=g.name) for g in film_model.genres]
    actors = [Person(uuid=a.id, full_name=a.name) for a in film_model.actors]
    writers = [Person(uuid=w.id, full_name=w.name) for w in film_model.writers]
    directors = [Person(uuid=d.id, full_name=d.name) for d in film_model.directors]
    return Film(
        id=film_model.id,
        title=film_model.title,
        imdb_rating=film_model.imdb_rating,
        description=film_model.description,
        genre=genres,
        actors=actors,
        writers=writers,
        directors=directors
    )

def _transform_to_short_film_response(film_model: FilmModel) -> FilmShort:
    return FilmShort(
        id=film_model.id,
        title=film_model.title,
        imdb_rating=film_model.imdb_rating
    )


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film: FilmModel = await film_service.get_by_id(film_id)
    print(film)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return _transform_to_film_response(film)



@router.get('/', response_model=list[FilmShort])
async def films_list(
    sort: Optional[str] = Query(None, description="Sort field (e.g., -imdb_rating)"),
    genre: Optional[str] = Query(None, description="Filter by genre UUID"),
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> list[FilmShort]:
    films: list[FilmModel] = await film_service.get_films(
        sort=sort,
        genre=genre,
        page_number=page_number,
        page_size=page_size
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='films not found'
        )
    
    return [_transform_to_short_film_response(film) for film in films]
    
    
@router.get('/search/', response_model=list[FilmShort])
async def films_search(
    query: Optional[str] = Query(None, description="Search in film title"),
    sort: Optional[str] = Query(None, description="Sort field (e.g., -imdb_rating)"),
    genre: Optional[str] = Query(None, description="Filter by genre UUID"),
    page_number: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    film_service: FilmService = Depends(get_film_service)
) -> list[FilmShort]:
    films: list[FilmModel] = await film_service.get_films(
        query=query,
        sort=sort,
        genre=genre,
        page_number=page_number,
        page_size=page_size
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='No searched films. Try another query.')
        
    return [_transform_to_short_film_response(film) for film in films]