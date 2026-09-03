from enum import Enum
from http import HTTPStatus
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from src.models.film import FilmModel
from src.services.film import FilmService, get_film_service
from src.api.v1.utils import FilmTransformer
from src.api.v1.models import Film, FilmShort
from src.core.auth import get_current_user, AuthPayload


router = APIRouter()


class PaginationParams:
    def __init__(
        self,
        page_number: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size"),
    ):
        self.page_number = page_number
        self.page_size = page_size

@router.get(
    "/",
    response_model=list[FilmShort],
    summary="Получить список фильмов",
    description="""
    Возвращает список фильмов с поддержкой:
    - Сортировки по рейтингу или названию
    - Фильтрации по жанру
    - Пагинации
    """,
    response_description="Список фильмов с краткой информацией",
    tags=["Фильмы"]
)
async def films_list(
    sort: Optional[str] = Query(None, description="Sort field (e.g., -imdb_rating)"),
    genre: Optional[str] = Query(None, description="Filter by genre UUID"),
    pagination: PaginationParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
    current_user: AuthPayload = Depends(get_current_user),
) -> list[FilmShort]:
    films: list[FilmModel] = await film_service.get_films(
        sort=sort, 
        genre=genre, 
        page_number=pagination.page_number, 
        page_size=pagination.page_size
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="films not found"
        )
    return FilmTransformer.to_films_short(films)


@router.get(
    "/search/",
    response_model=list[FilmShort],
    summary="Поиск фильмов",
    description="""
    Поиск фильмов по названию и описанию с поддержкой:
    - Полнотекстового поиска
    - Сортировки результатов
    - Фильтрации по жанру
    - Пагинации
    """,
    response_description="Список фильмов по результатам поиска",
    tags=["Поиск"]
)
async def films_search(
    query: Optional[str] = Query(None, description="Search in film title"),
    sort: Optional[str] = Query(None, description="Sort field (e.g., -imdb_rating)"),
    genre: Optional[str] = Query(None, description="Filter by genre UUID"),
    pagination: PaginationParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
    current_user: AuthPayload = Depends(get_current_user),
) -> list[FilmShort]:
    films: list[FilmModel] = await film_service.get_films(
        query=query,
        sort=sort,
        genre=genre,
        page_number=pagination.page_number,
        page_size=pagination.page_size,
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="No searched films. Try another query.",
        )
    return FilmTransformer.to_films_short(films)



@router.get(
    "/{film_id}/",
    response_model=Film,
    summary="Получить детальную информацию о фильме",
    description="Возвращает полную информацию о фильме по его id",
    response_description="Детальная информация о фильме",
    tags=["Фильмы"]
)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service),
    current_user: AuthPayload = Depends(get_current_user),
) -> Film:
    film: FilmModel | None = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="film not found"
        )
    return FilmTransformer.to_film(film)
