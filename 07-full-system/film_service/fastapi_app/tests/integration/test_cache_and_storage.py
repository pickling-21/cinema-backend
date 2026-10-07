"""Integration tests: FilmService + RedisCache + ElasticStorage working together.

Only the two external servers are replaced (fakeredis, FakeElastic); every
class of the service itself is the real one.
"""
import json

import pytest

from fakes import make_film
from src.db.elastic import ElasticStorage
from src.db.redis import RedisCache
from src.models.film import FilmModel
from src.services.film import FILM_CACHE_TTL, FILMS_CACHE_TTL, FilmService


@pytest.fixture
def cache(fake_redis) -> RedisCache:
    return RedisCache(redis=fake_redis, film_ttl=FILM_CACHE_TTL, films_ttl=FILMS_CACHE_TTL)


@pytest.fixture
def service(fake_es, cache) -> FilmService:
    return FilmService(storage=ElasticStorage(es=fake_es), cache=cache)


async def test_redis_cache_film_roundtrip_and_ttl(cache, fake_redis, film_model):
    assert await cache.get_film(film_model.id) is None
    await cache.set_film(film_model)
    assert await cache.get_film(film_model.id) == film_model
    assert 0 < await fake_redis.ttl(f"film:{film_model.id}") <= FILM_CACHE_TTL


async def test_redis_cache_explicit_ttl_overrides_default(cache, fake_redis, film_model):
    await cache.set_film(film_model, ttl_seconds=5)
    await cache.set_films("k", [film_model], ttl_seconds=7)
    assert await fake_redis.ttl(f"film:{film_model.id}") <= 5
    assert await fake_redis.ttl("k") <= 7


async def test_redis_cache_list_roundtrip(cache, fake_redis, film_model):
    assert await cache.get_films("films:key") is None
    await cache.set_films("films:key", [film_model])
    assert await cache.get_films("films:key") == [film_model]
    assert 0 < await fake_redis.ttl("films:key") <= FILMS_CACHE_TTL


async def test_film_is_read_from_storage_once_then_from_cache(service, fake_es, fake_redis, film_dict):
    fake_es.add(film_dict)

    first = await service.get_by_id(film_dict["id"])
    fake_es.docs.clear()  # storage "loses" the film: only the cache can answer now
    second = await service.get_by_id(film_dict["id"])

    assert first == second == FilmModel(**film_dict)
    assert fake_es.get_calls == 1
    assert await fake_redis.exists(f"film:{film_dict['id']}") == 1


async def test_unknown_film_leaves_cache_empty(service, fake_es, fake_redis):
    assert await service.get_by_id("missing") is None
    assert await fake_redis.dbsize() == 0
    assert fake_es.get_calls == 1


async def test_film_list_is_cached_under_parameter_key(service, fake_es, fake_redis):
    fake_es.add(*(make_film(f"Film {i}", rating=5 + i) for i in range(5)))

    first = await service.get_films(sort="-imdb_rating", page_size=3)
    second = await service.get_films(sort="-imdb_rating", page_size=3)

    assert [f.imdb_rating for f in first] == [9, 8, 7]
    assert first == second
    assert fake_es.search_calls == 1
    raw = await fake_redis.get("films:-imdb_rating:no_genre:no_query:3:1")
    assert [item["imdb_rating"] for item in json.loads(raw)] == [9, 8, 7]


async def test_different_parameters_do_not_share_a_cache_entry(service, fake_es):
    fake_es.add(*(make_film(f"Film {i}", rating=5 + i) for i in range(5)))

    page1 = await service.get_films(sort="imdb_rating", page_size=2, page_number=1)
    page2 = await service.get_films(sort="imdb_rating", page_size=2, page_number=2)

    assert [f.imdb_rating for f in page1] == [5, 6]
    assert [f.imdb_rating for f in page2] == [7, 8]
    assert fake_es.search_calls == 2


async def test_empty_search_result_is_cached_too(service, fake_es):
    assert await service.get_films(query="nothing") == []
    assert await service.get_films(query="nothing") == []
    assert fake_es.search_calls == 1
