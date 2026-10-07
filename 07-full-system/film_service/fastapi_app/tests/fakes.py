"""Fakes and data builders for the in-process test suite.

Nothing here needs Docker: Redis is replaced by fakeredis and Elasticsearch
by a small in-memory fake that understands the query body built by
ElasticStorage._build_query.
"""
import time
import uuid

import jwt
from elastic_transport import ApiResponseMeta, HttpHeaders, NodeConfig
from elasticsearch import NotFoundError

from src.core.config import settings


class FakeElastic:
    """In-memory stand-in for AsyncElasticsearch (get / search / close only)."""

    def __init__(self):
        self.docs: dict[str, dict] = {}
        self.get_calls = 0
        self.search_calls = 0
        self.closed = False

    def add(self, *films: dict) -> None:
        for film in films:
            self.docs[film["id"]] = film

    async def get(self, index: str, id: str) -> dict:
        self.get_calls += 1
        if id not in self.docs:
            meta = ApiResponseMeta(
                status=404,
                http_version="1.1",
                headers=HttpHeaders(),
                duration=0.0,
                node=NodeConfig("http", "localhost", 9200),
            )
            raise NotFoundError("not found", meta, {"found": False})
        return {"_id": id, "_source": self.docs[id]}

    async def search(self, index: str, body: dict) -> dict:
        self.search_calls += 1
        docs = list(self.docs.values())

        must = body["query"]["bool"]["must"][0]
        if "multi_match" in must:
            words = must["multi_match"]["query"].lower().split()
            docs = [
                d for d in docs
                if any(
                    w in f'{d["title"]} {d.get("description") or ""}'.lower().split()
                    for w in words
                )
            ]

        for flt in body["query"]["bool"]["filter"]:
            genre_id = flt["nested"]["query"]["term"]["genres.id"]
            docs = [d for d in docs if any(g["id"] == genre_id for g in d["genres"])]

        for clause in reversed(body["sort"]):
            (field, opts), = clause.items()
            key = "title" if field == "title.raw" else field
            docs.sort(key=lambda d: d[key], reverse=opts["order"] == "desc")

        start = body["from"]
        page = docs[start:start + body["size"]]
        return {"hits": {"hits": [{"_id": d["id"], "_source": d} for d in page]}}

    async def close(self) -> None:
        self.closed = True


def make_film(title: str = "The Star", rating: float | None = 8.5, **overrides) -> dict:
    film = {
        "id": str(uuid.uuid4()),
        "imdb_rating": rating,
        "title": title,
        "description": "New World",
        "genres": [{"id": str(uuid.uuid4()), "name": "Action"}],
        "genres_names": ["Action"],
        "directors": [{"id": str(uuid.uuid4()), "name": "Stan"}],
        "directors_names": ["Stan"],
        "actors": [{"id": str(uuid.uuid4()), "name": "Ann"}],
        "actors_names": ["Ann"],
        "writers": [{"id": str(uuid.uuid4()), "name": "Ben"}],
        "writers_names": ["Ben"],
    }
    film.update(overrides)
    return film


def make_token(
    sub: str | None = "user-1",
    role: str | None = "subscriber",
    jti: str | None = "jti-1",
    exp_delta: int = 600,
    secret: str | None = None,
    algorithm: str = "HS256",
) -> str:
    payload: dict = {"exp": int(time.time()) + exp_delta}
    if sub is not None:
        payload["sub"] = sub
    if role is not None:
        payload["role"] = role
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, secret or settings.JWT_SECRET_KEY, algorithm=algorithm)
