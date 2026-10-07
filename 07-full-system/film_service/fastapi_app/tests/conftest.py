"""Shared fixtures for the in-process test suite (unit, integration, system)."""
import pytest
from fakeredis import FakeAsyncRedis

from fakes import FakeElastic, make_film
from src.models.film import FilmModel


@pytest.fixture
def film_dict() -> dict:
    return make_film()


@pytest.fixture
def film_model(film_dict) -> FilmModel:
    return FilmModel(**film_dict)


@pytest.fixture
def fake_es() -> FakeElastic:
    return FakeElastic()


@pytest.fixture
async def fake_redis():
    client = FakeAsyncRedis()
    yield client
    await client.aclose()
