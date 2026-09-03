from abc import ABC, abstractmethod
from src.models.film import FilmModel
from typing import Optional

class BaseCache(ABC):
    @abstractmethod
    async def get_film(self, film_id: str) -> Optional[FilmModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def set_film(self, film: FilmModel, ttl_seconds: int) -> None:
        raise NotImplementedError
    
    @abstractmethod
    async def get_films(self, cache_key: str) -> Optional[list[FilmModel]]:
        raise NotImplementedError
    
    async def set_films(self, cache_key: str, films: list[FilmModel], ttl_seconds: int) -> None:
        raise NotImplementedError

