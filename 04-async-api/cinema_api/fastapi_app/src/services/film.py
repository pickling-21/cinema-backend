from functools import lru_cache
from typing import Optional
import json
from loguru import logger

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.film import FilmModel

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
FILMS_CACHE_EXPIRE_IN_SECONDS = 60 * 10  # 10 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    def _generate_cache_key(
        self,
        sort: str | None = None,
        genre: str | None = None,
        query: str | None = None,
        page_size: int = 50,
        page_number: int = 1,
        prefix: str = "films"
    ) -> str:
        """Генерирует уникальный ключ кэша на основе параметров"""
        key_parts = [prefix, sort or "no_sort", genre or "no_genre", query or "no_query", str(page_size), str(page_number)]
        return ":".join(key_parts)

    async def get_by_id(self, film_id: str) -> Optional[FilmModel]:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[FilmModel]:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            logger.warning(f"Film not found in Elasticsearch: {film_id}")
            return None
        return FilmModel(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[FilmModel]:
        data = await self.redis.get(film_id)
        if not data:
            return None
        film = FilmModel.model_validate_json(data)
        logger.info(f"Film  cache: {film_id}")
        return film

    async def _put_film_to_cache(self, film: FilmModel):
        film_json = film.model_dump_json()
        await self.redis.set(film.id, film_json, FILM_CACHE_EXPIRE_IN_SECONDS)

    @staticmethod
    def _create_es_search_body(
        sort: str | None = None,
        query: str | None = None,
        genre: str | None = None,
        page_number: int = 1,
        page_size: int = 50,
    ):
        if sort:
            sort_field = sort.lstrip("-")
            order = "desc" if sort.startswith("-") else "asc"
            if sort_field == "title":
                sort_field = "title.raw"
        else:
            sort_field, order = "imdb_rating", "desc"

        from_ = (page_number - 1) * page_size
        base_query = {"multi_match": {"query": query, "fields": ["title^2", "description"]}} if query else {"match_all": {}}
        bool_query = {"must": base_query}

        if genre:
            bool_query["filter"] = {
                "nested": {
                    "path": "genres",
                    "query": {"term": {"genres.id": genre}}
                }
            }

        return {
            "from": from_,
            "size": page_size,
            "sort": [{sort_field: {"order": order}}],
            "query": {"bool": bool_query}
        }

    async def get_films(
        self, 
        sort: str | None = None, 
        genre: str | None = None,
        query: str | None = None, 
        page_size: int = 50, 
        page_number: int = 1
    ) -> Optional[list[FilmModel]]:
        
        # генерируем ключ кэша
        cache_key = self._generate_cache_key(
            sort=sort,
            genre=genre,
            query=query,
            page_size=page_size,
            page_number=page_number,
            prefix="films"
        )
        
        # проверяем кэш
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Films list cache: {cache_key}")
            films_data = json.loads(cached_data)
            return [FilmModel(**film) for film in films_data]
        
        es_query = self._create_es_search_body(
            sort=sort,
            query=query, 
            genre=genre,
            page_number=page_number,
            page_size=page_size
        )
        
        logger.debug(f" sort={sort}, genre={genre}, query={query}")
        response = await self.elastic.search(index="movies", body=es_query)
        
        films = []
        for hit in response['hits']['hits']:
            film_data = hit['_source']
            films.append(FilmModel(**film_data))
        
        logger.info(f"Found {len(films)} films in Elasticsearch")
        
        films_json = json.dumps([film.model_dump() for film in films])
        await self.redis.set(cache_key, films_json, FILMS_CACHE_EXPIRE_IN_SECONDS)
        
        return films


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
