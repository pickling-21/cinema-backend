"""Unit tests for src.db.elastic.ElasticStorage."""
from unittest.mock import AsyncMock

import pytest

from src.db.elastic import ElasticStorage


def test_build_query_defaults():
    assert ElasticStorage._build_query(None, None, None, 1, 50) == {
        "from": 0,
        "size": 50,
        "sort": [],
        "query": {"bool": {"must": [{"match_all": {}}], "filter": []}},
    }


@pytest.mark.parametrize(
    "sort, expected",
    [
        ("imdb_rating", [{"imdb_rating": {"order": "asc"}}]),
        ("-imdb_rating", [{"imdb_rating": {"order": "desc"}}]),
        ("title", [{"title.raw": {"order": "asc"}}]),
        ("-title", [{"title.raw": {"order": "desc"}}]),
    ],
)
def test_build_query_sort(sort, expected):
    assert ElasticStorage._build_query(None, sort, None, 1, 50)["sort"] == expected


def test_build_query_text_search_and_genre_filter():
    body = ElasticStorage._build_query("star wars", None, "genre-1", 1, 50)
    assert body["query"]["bool"]["must"] == [
        {"multi_match": {"query": "star wars", "fields": ["title^2", "description"]}}
    ]
    assert body["query"]["bool"]["filter"] == [
        {"nested": {"path": "genres", "query": {"term": {"genres.id": "genre-1"}}}}
    ]


@pytest.mark.parametrize("page, size, offset", [(1, 50, 0), (2, 15, 15), (3, 25, 50)])
def test_build_query_pagination_offset(page, size, offset):
    body = ElasticStorage._build_query(None, None, None, page, size)
    assert (body["from"], body["size"]) == (offset, size)


async def test_get_film_found(fake_es, film_dict):
    fake_es.add(film_dict)
    film = await ElasticStorage(es=fake_es).get_film(film_dict["id"])
    assert film.id == film_dict["id"] and film.title == film_dict["title"]


async def test_get_film_not_found_returns_none(fake_es):
    assert await ElasticStorage(es=fake_es).get_film("missing") is None


async def test_set_film_indexes_document(film_model):
    es = AsyncMock()
    await ElasticStorage(es=es, index_name="movies").set_film(film_model)
    es.index.assert_awaited_once_with(index="movies", id=film_model.id, document=film_model.model_dump())


async def test_search_films_maps_hits_to_models(film_dict):
    es = AsyncMock()
    es.search.return_value = {"hits": {"hits": [{"_source": film_dict}]}}
    films = await ElasticStorage(es=es, index_name="movies").search_films("star", "-imdb_rating", None, 2, 10)
    assert [f.id for f in films] == [film_dict["id"]]
    kwargs = es.search.await_args.kwargs
    assert kwargs["index"] == "movies" and kwargs["body"]["from"] == 10
