"""Unit tests for src.api.v1.utils.FilmTransformer."""
from src.api.v1.utils import FilmTransformer


def test_to_film_maps_nested_entities(film_model):
    film = FilmTransformer.to_film(film_model)
    assert film.uuid == film_model.id
    assert film.title == film_model.title
    assert [g.name for g in film.genre] == ["Action"]
    assert [p.full_name for p in film.actors] == ["Ann"]
    assert [p.full_name for p in film.writers] == ["Ben"]
    assert [p.full_name for p in film.directors] == ["Stan"]


def test_to_film_short_keeps_three_fields(film_model):
    short = FilmTransformer.to_film_short(film_model)
    assert short.model_dump() == {
        "uuid": film_model.id,
        "title": film_model.title,
        "imdb_rating": film_model.imdb_rating,
    }


def test_to_films_short_handles_empty_and_many(film_model):
    assert FilmTransformer.to_films_short([]) == []
    assert len(FilmTransformer.to_films_short([film_model, film_model])) == 2
