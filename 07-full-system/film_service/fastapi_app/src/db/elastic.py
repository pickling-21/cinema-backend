from typing import Optional
from elasticsearch import AsyncElasticsearch, NotFoundError
from src.models.film import FilmModel
from src.db.base_storage import BaseStorage

class ElasticStorage(BaseStorage):
    def __init__(self, es: AsyncElasticsearch, index_name: str = "movies"):
        self._es = es
        self._index = index_name

    async def get_film(self, film_id: str) -> Optional[FilmModel]:
        try:
            doc = await self._es.get(index=self._index, id=film_id)
        except NotFoundError:
            return None
        return FilmModel(**doc['_source'])

    async def set_film(self, film: FilmModel) -> None:
        await self._es.index(index=self._index, id=film.id, document=film.model_dump())
        return

    @staticmethod
    def _build_query(
        query: Optional[str],
        sort: Optional[str],
        genre: Optional[str],
        page_number: int,
        page_size: int,
    ) -> dict:
        if sort:
            sort_field = sort.lstrip('-')
            order = "desc" if sort.startswith('-') else "asc"
            if sort_field == "title":
                sort_field = "title.raw"
            sort_clause = [{sort_field: {"order": order}}]
        else:
            sort_clause = []

        if query:
            base_query = {"multi_match": {"query": query, "fields": ["title^2", "description"]}}
        else:
            base_query = {"match_all": {}}

        must = [base_query]
        filters = []
        if genre:
            filters.append({
                "nested": {
                    "path": "genres",
                    "query": {"term": {"genres.id": genre}}
                }
            })

        es_query = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "sort": sort_clause,
            "query": {"bool": {"must": must, "filter": filters}},
        }
        return es_query

    async def search_films(
        self,
        query: Optional[str],
        sort: Optional[str],
        genre: Optional[str],
        page_number: int,
        page_size: int,
    ) -> list[FilmModel]:
        body = self._build_query(query, sort, genre, page_number, page_size)
        resp = await self._es.search(index=self._index, body=body)
        hits = resp["hits"]["hits"]
        return [FilmModel(**h["_source"]) for h in hits]

es: Optional[AsyncElasticsearch] = None
async def get_elastic() -> AsyncElasticsearch:
    return es