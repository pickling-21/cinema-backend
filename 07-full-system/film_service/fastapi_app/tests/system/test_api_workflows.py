"""System tests: the whole FastAPI application driven through HTTP.

The app is started with its real lifespan, routing, auth dependency, service,
cache and storage classes. Only the Redis and Elasticsearch servers are
replaced by in-memory fakes, so the suite runs without Docker.
"""
import httpx
import pytest
from fakeredis import FakeAsyncRedis

import main
from fakes import FakeElastic, make_film, make_token
from src.db import elastic, redis
from src.services.film import get_film_service

API = "/api/v1/films"


@pytest.fixture
async def system(monkeypatch):
    """Running app + handles to its fake infrastructure."""
    fake_es = FakeElastic()
    monkeypatch.setattr(main, "Redis", lambda host, port, db: FakeAsyncRedis(db=db))
    monkeypatch.setattr(main, "AsyncElasticsearch", lambda hosts: fake_es)
    get_film_service.cache_clear()

    async with main.app.router.lifespan_context(main.app):
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, fake_es, redis.auth_redis
    assert fake_es.closed


def auth(**claims) -> dict:
    return {"Authorization": f"Bearer {make_token(**claims)}"}


async def test_root_is_public(system):
    client, _, _ = system
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Cinema API is running!"}


@pytest.mark.parametrize("path", [f"{API}/", f"{API}/search/", f"{API}/some-id/"])
async def test_every_film_endpoint_requires_a_token(system, path):
    client, _, _ = system
    resp = await client.get(path)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authorization header required"


async def test_film_details_workflow(system):
    client, fake_es, _ = system
    film = make_film("The Super Star", rating=9.1)
    fake_es.add(film)

    resp = await client.get(f"{API}/{film['id']}/", headers=auth())

    assert resp.status_code == 200
    body = resp.json()
    # The response models call this field `uuid` but declare alias="id",
    # and FastAPI serialises by alias, so the wire name is "id".
    assert body["id"] == film["id"]
    assert "uuid" not in body
    assert body["title"] == "The Super Star"
    assert body["imdb_rating"] == 9.1
    assert [g["name"] for g in body["genre"]] == ["Action"]
    assert {"actors", "writers", "directors", "description"} <= body.keys()


async def test_unknown_film_returns_404(system):
    client, _, _ = system
    resp = await client.get(f"{API}/no-such-film/", headers=auth())
    assert resp.status_code == 404
    assert resp.json()["detail"] == "film not found"


async def test_second_request_is_served_from_cache(system):
    client, fake_es, _ = system
    film = make_film()
    fake_es.add(film)

    first = await client.get(f"{API}/{film['id']}/", headers=auth())
    fake_es.docs.clear()
    second = await client.get(f"{API}/{film['id']}/", headers=auth())

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert fake_es.get_calls == 1


@pytest.mark.parametrize(
    "params, expected_ratings",
    [
        ({"sort": "-imdb_rating", "page_size": 3}, [9.0, 8.0, 7.0]),
        ({"sort": "imdb_rating", "page_size": 2, "page_number": 2}, [7.0, 8.0]),
        ({"sort": "imdb_rating", "page_size": 3, "page_number": 2}, [8.0, 9.0]),
    ],
)
async def test_film_list_sorting_and_pagination(system, params, expected_ratings):
    client, fake_es, _ = system
    fake_es.add(*(make_film(f"Film {i}", rating=5.0 + i) for i in range(5)))

    resp = await client.get(f"{API}/", params=params, headers=auth())

    assert resp.status_code == 200
    assert [f["imdb_rating"] for f in resp.json()] == expected_ratings
    assert set(resp.json()[0]) == {"id", "title", "imdb_rating"}


async def test_film_list_page_beyond_data_returns_404(system):
    client, fake_es, _ = system
    fake_es.add(make_film())
    resp = await client.get(f"{API}/", params={"page_number": 3}, headers=auth())
    assert resp.status_code == 404
    assert resp.json()["detail"] == "films not found"


async def test_film_list_genre_filter(system):
    client, fake_es, _ = system
    comedy = make_film("Funny", genres=[{"id": "genre-comedy", "name": "Comedy"}])
    fake_es.add(comedy, make_film("Serious"))

    resp = await client.get(f"{API}/", params={"genre": "genre-comedy"}, headers=auth())

    assert resp.status_code == 200
    assert [f["title"] for f in resp.json()] == ["Funny"]


async def test_search_workflow(system):
    client, fake_es, _ = system
    fake_es.add(make_film("The Star 1", rating=7.0), make_film("The Star 2", rating=9.0), make_film("Moon"))

    found = await client.get(
        f"{API}/search/", params={"query": "star", "sort": "-imdb_rating"}, headers=auth()
    )
    missing = await client.get(f"{API}/search/", params={"query": "Mashed potato"}, headers=auth())

    assert found.status_code == 200
    assert [f["title"] for f in found.json()] == ["The Star 2", "The Star 1"]
    assert missing.status_code == 404
    assert missing.json()["detail"] == "No searched films. Try another query."


@pytest.mark.parametrize(
    "params",
    [{"page_size": 0}, {"page_size": 101}, {"page_number": 0}, {"page_size": "ten"}],
)
async def test_invalid_pagination_is_rejected_before_reaching_storage(system, params):
    client, fake_es, _ = system
    resp = await client.get(f"{API}/", params=params, headers=auth())
    assert resp.status_code == 422
    assert fake_es.search_calls == 0


@pytest.mark.parametrize(
    "headers, detail",
    [
        ({"Authorization": "Bearer not-a-jwt"}, "Invalid token"),
        (auth(exp_delta=-5), "Token has expired"),
        (auth(jti=None), "Token missing jti claim"),
    ],
    ids=["garbage", "expired", "no-jti"],
)
async def test_bad_tokens_never_reach_film_data(system, headers, detail):
    client, fake_es, _ = system
    film = make_film()
    fake_es.add(film)

    resp = await client.get(f"{API}/{film['id']}/", headers=headers)

    assert resp.status_code == 401
    assert resp.json()["detail"] == detail
    assert fake_es.get_calls == 0


async def test_logout_revokes_access_end_to_end(system):
    """A token works until the auth service blacklists its jti in Redis DB 1."""
    client, fake_es, auth_redis = system
    film = make_film()
    fake_es.add(film)
    headers = auth(jti="session-42")

    before = await client.get(f"{API}/{film['id']}/", headers=headers)
    await auth_redis.set("blacklist:session-42", "1")  # what auth_service does on logout
    after = await client.get(f"{API}/{film['id']}/", headers=headers)

    assert before.status_code == 200
    assert after.status_code == 401
    assert after.json()["detail"] == "Token has been revoked"
