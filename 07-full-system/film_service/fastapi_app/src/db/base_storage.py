from abc import ABC, abstractmethod
from typing import Optional, Any
from src.models.film import FilmModel
class BaseStorage(ABC):

    @abstractmethod
    async def get_film(self, film_id: str) -> Optional[FilmModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def search_films(
        self,
        query: Optional[str],
        sort: Optional[str],
        genre: Optional[str],
        page_number: int,
        page_size: int,
    ) -> list[FilmModel]:
        raise NotImplementedError