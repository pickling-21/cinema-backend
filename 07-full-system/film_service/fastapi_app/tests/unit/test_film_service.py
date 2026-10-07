"""Unit tests for src.services.film.FilmService with mocked cache and storage."""
from unittest.mock import AsyncMock

import pytest

from src.db.elastic import ElasticStorage
from src.db.redis import RedisCache
from src.services.film import FilmService, get_film_service


@pytest.fixture
def cache() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def storage() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(storage, cache) -> FilmService:
    return FilmService(storage=storage, cache=cache)


async def test_get_by_id_cache_hit_skips_storage(service, cache, storage, film_model):
    cache.get_film.return_value = film_model
    assert await service.get_by_id(film_model.id) is film_model
    storage.get_film.assert_not_awaited()
    cache.set_film.assert_not_awaited()


async def test_get_by_id_cache_miss_reads_storage_and_fills_cache(service, cache, storage, film_model):
    cache.get_film.return_value = None
    storage.get_film.return_value = film_model
    assert await service.get_by_id(film_model.id) is film_model
    storage.get_film.assert_awaited_once_with(film_model.id)
    cache.set_film.assert_awaited_once_with(film_model)


async def test_get_by_id_unknown_film_is_not_cached(service, cache, storage):
    cache.get_film.return_value = None
    storage.get_film.return_value = None
    assert await service.get_by_id("missing") is None
    cache.set_film.assert_not_awaited()


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, "films:no_sort:no_genre:no_query:50:1"),
        (
            {"sort": "-imdb_rating", "genre": "g1", "query": "star", "page_size": 20, "page_number": 3},
            "films:-imdb_rating:g1:star:20:3",
        ),
        ({"prefix": "search", "query": "star"}, "search:no_sort:no_genre:star:50:1"),
    ],
)
def test_generate_cache_key(kwargs, expected):
    assert FilmService._generate_cache_key(**kwargs) == expected


async def test_get_films_cache_hit_skips_storage(service, cache, storage, film_model):
    cache.get_films.return_value = [film_model]
    assert await service.get_films(sort="title") == [film_model]
    cache.get_films.assert_awaited_once_with("films:title:no_genre:no_query:50:1")
    storage.search_films.assert_not_awaited()


async def test_get_films_cached_empty_list_is_a_hit(service, cache, storage):
    cache.get_films.return_value = []
    assert await service.get_films() == []
    storage.search_films.assert_not_awaited()


async def test_get_films_cache_miss_searches_and_caches(service, cache, storage, film_model):
    cache.get_films.return_value = None
    storage.search_films.return_value = [film_model]
    result = await service.get_films(sort="-imdb_rating", genre="g1", query="star", page_number=2, page_size=10)
    assert result == [film_model]
    storage.search_films.assert_awaited_once_with("star", "-imdb_rating", "g1", 2, 10)
    cache.set_films.assert_awaited_once_with("films:-imdb_rating:g1:star:10:2", [film_model])


def test_factory_wires_redis_cache_and_elastic_storage():
    redis, elastic = object(), object()
    service = get_film_service(redis=redis, elastic=elastic)
    assert isinstance(service._cache, RedisCache)
    assert isinstance(service._storage, ElasticStorage)
    assert get_film_service(redis=redis, elastic=elastic) is service
