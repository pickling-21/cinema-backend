from functools import lru_cache
from typing import Optional
from fastapi import Depends
from src.models.film import FilmModel

from src.db.base_cache import BaseCache
from src.db.base_storage import BaseStorage
from src.db.redis import RedisCache
from src.db.elastic import ElasticStorage
from src.db.redis import get_redis
from src.db.elastic import get_elastic

FILM_CACHE_TTL = 60 * 5
FILMS_CACHE_TTL = 60 * 10


class FilmService:
    def __init__(self, storage: BaseStorage, cache: BaseCache):
        self._storage = storage
        self._cache = cache

    async def get_by_id(self, film_id: str) -> Optional[FilmModel]:
        film = await self._cache.get_film(film_id)
        if film:
            return film
        film = await self._storage.get_film(film_id)
        if film:
            await self._cache.set_film(film)
        return film

    @staticmethod
    def _generate_cache_key(
        sort: str | None = None,
        genre: str | None = None,
        query: str | None = None,
        page_size: int = 50,
        page_number: int = 1,
        prefix: str = "films",
    ) -> str:
        """Генерирует уникальный ключ кэша на основе параметров"""
        key_parts = [
            prefix,
            sort or "no_sort",
            genre or "no_genre",
            query or "no_query",
            str(page_size),
            str(page_number),
        ]
        return ":".join(key_parts)

    async def get_films(
        self,
        sort: str | None = None,
        genre: str | None = None,
        query: str | None = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> list[FilmModel]:
        cache_key = self._generate_cache_key(sort, genre, query, page_size, page_number)
        cached = await self._cache.get_films(cache_key)
        if cached is not None:
            return cached

        films = await self._storage.search_films(query, sort, genre, page_number, page_size)
        await self._cache.set_films(cache_key, films)
        return films

@lru_cache
def get_film_service(
    redis = Depends(get_redis),
    elastic = Depends(get_elastic),
) -> FilmService:
    cache = RedisCache(redis=redis, film_ttl=FILM_CACHE_TTL, films_ttl=FILMS_CACHE_TTL)
    storage = ElasticStorage(es=elastic, index_name="movies")
    return FilmService(storage=storage, cache=cache)
