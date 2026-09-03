from src.models.film import FilmModel
from src.api.v1.models import Film, FilmShort, Genre, Person

class FilmTransformer:
    @staticmethod
    def to_film(film_model: FilmModel) -> Film:
        """Трансформация в полное представление"""
        genres = [Genre(uuid=g.id, name=g.name) for g in film_model.genres]
        actors = [Person(uuid=a.id, full_name=a.name) for a in film_model.actors]
        writers = [Person(uuid=w.id, full_name=w.name) for w in film_model.writers]
        directors = [Person(uuid=d.id, full_name=d.name) for d in film_model.directors]
        return Film(
            id=film_model.id,
            title=film_model.title,
            imdb_rating=film_model.imdb_rating,
            description=film_model.description,
            genre=genres,
            actors=actors,
            writers=writers,
            directors=directors,
        )

    @staticmethod
    def to_film_short(film_model: FilmModel) -> FilmShort:
        """Трансформация в краткое представление"""
        return FilmShort(
            id=film_model.id,
            title=film_model.title,
            imdb_rating=film_model.imdb_rating,
        )

    @staticmethod
    def to_films_short(films: list[FilmModel]) -> list[FilmShort]:
        """Трансформация списка в краткие представления"""
        return [FilmTransformer.to_film_short(film) for film in films]
