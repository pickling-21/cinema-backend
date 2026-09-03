import json
from typing import Optional
from redis.asyncio import Redis
from src.models.film import FilmModel
from src.db.base_cache import BaseCache

class RedisCache(BaseCache):
    def __init__(self, redis: Redis, film_ttl: int, films_ttl: int):
        self._redis = redis
        self._film_ttl = film_ttl
        self._films_ttl = films_ttl

    async def get_film(self, film_id: str) -> Optional[FilmModel]:
        raw = await self._redis.get(f"film:{film_id}")
        if not raw:
            return None
        return FilmModel.model_validate_json(raw)

    async def set_film(self, film: FilmModel, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._film_ttl
        await self._redis.set(f"film:{film.id}", film.model_dump_json(), ex=ttl)

    async def get_films(self, cache_key: str) -> Optional[list[FilmModel]]:
        raw = await self._redis.get(cache_key)
        if not raw:
            return None
        data = json.loads(raw)
        return [FilmModel(**item) for item in data]

    async def set_films(self, cache_key: str, films: list[FilmModel], ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._films_ttl
        payload = json.dumps([f.model_dump() for f in films])
        await self._redis.set(cache_key, payload, ex=ttl)


redis: Optional[Redis] = None


async def get_redis() -> Redis:
    return redis