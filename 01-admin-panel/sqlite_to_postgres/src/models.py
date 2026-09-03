from dataclasses import dataclass, fields
from datetime import date, datetime
from typing import Any, Callable, Optional
from uuid import UUID


def convert_fields(
    obj: Any, field_mapping: dict[str, str], converter: Callable[[str], Any]
) -> None:
    for sqlite_field, dataclass_field in field_mapping.items():
        value = getattr(obj, dataclass_field)
        if not isinstance(value, str):
            continue
        setattr(obj, dataclass_field, converter(value))


# Маппинг таблиц
DATACLASS_TABLE_MAP = {
    "Person": "person",
    "Genre": "genre",
    "FilmWork": "film_work",
    "GenreFilmWork": "genre_film_work",
    "PersonFilmWork": "person_film_work",
}

# Маппинг полей между SQLite и датаклассами
FIELD_MAPPING = {
    "person": {
        "id": "id",
        "full_name": "full_name",
        "created_at": "created",
        "updated_at": "modified",
    },
    "genre": {
        "id": "id",
        "name": "name",
        "description": "description",
        "created_at": "created",
        "updated_at": "modified",
    },
    "film_work": {
        "id": "id",
        "title": "title",
        "description": "description",
        "creation_date": "creation_date",
        "rating": "rating",
        "type": "type",
        "created_at": "created",
        "updated_at": "modified",
    },
    "genre_film_work": {
        "id": "id",
        "film_work_id": "film_work_id",
        "genre_id": "genre_id",
        "created_at": "created",
    },
    "person_film_work": {
        "id": "id",
        "film_work_id": "film_work_id",
        "person_id": "person_id",
        "role": "role",
        "created_at": "created",
    },
}


@dataclass
class BaseMoviesDataClass:
    @classmethod
    def get_table_name(cls) -> str:
        class_name = cls.__name__
        return DATACLASS_TABLE_MAP.get(class_name, class_name.lower())

    @classmethod
    def get_fields(cls) -> list[str]:
        return [field.name for field in fields(cls)]

    @classmethod
    def get_sqlite_fields(cls) -> list[str]:
        table_name = cls.get_table_name()
        return list(FIELD_MAPPING.get(table_name, {}).keys())

    def __post_init__(self):
        convert_fields(self, {"id": "id"}, UUID)
        convert_fields(self, {"created_at": "created"}, datetime.fromisoformat)


@dataclass
class FilmWork(BaseMoviesDataClass):
    id: UUID
    title: str
    type: str
    created: datetime
    description: Optional[str] = None
    creation_date: Optional[date] = None
    rating: Optional[float] = None
    modified: Optional[datetime] = None

    def __post_init__(self):
        super().__post_init__()
        convert_fields(self, {"updated_at": "modified"}, datetime.fromisoformat)
        if self.creation_date and isinstance(self.creation_date, str):
            self.creation_date = date.fromisoformat(self.creation_date)


@dataclass
class Genre(BaseMoviesDataClass):
    id: UUID
    name: str
    created: datetime
    description: Optional[str] = None
    modified: Optional[datetime] = None

    def __post_init__(self):
        super().__post_init__()
        convert_fields(self, {"updated_at": "modified"}, datetime.fromisoformat)


@dataclass
class Person(BaseMoviesDataClass):
    id: UUID
    full_name: str
    created: datetime
    modified: Optional[datetime] = None

    def __post_init__(self):
        super().__post_init__()
        convert_fields(self, {"updated_at": "modified"}, datetime.fromisoformat)


@dataclass
class GenreFilmWork(BaseMoviesDataClass):
    id: UUID
    genre_id: UUID
    film_work_id: UUID
    created: datetime

    def __post_init__(self):
        super().__post_init__()
        convert_fields(
            self, {"genre_id": "genre_id", "film_work_id": "film_work_id"}, UUID
        )
        convert_fields(self, {"created_at": "created"}, datetime.fromisoformat)


@dataclass
class PersonFilmWork(BaseMoviesDataClass):
    id: UUID
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime

    def __post_init__(self):
        super().__post_init__()
        convert_fields(
            self,
            {
                "person_id": "person_id",
                "film_work_id": "film_work_id",
            },
            UUID,
        )
        convert_fields(self, {"created_at": "created"}, datetime.fromisoformat)
