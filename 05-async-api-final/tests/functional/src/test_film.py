import uuid
import pytest
from functional.settings import test_settings

pytestmark = pytest.mark.asyncio

@pytest.mark.parametrize(
    'film_id, expected_answer',
    [
        ('valid_id', {'status': 200, 'has_title': True}),
        ('invalid-123', {'status': 404}),
    ]
)
async def test_film_details(generate_film_data, make_bulk_query, make_get_request, es_write_data, film_id, expected_answer):
    test_id = str(uuid.uuid4())
    films = generate_film_data(2, 'The Super Start')

    if film_id == 'valid_id':
        films[0]['id'] = test_id
        
    bulk_query = make_bulk_query(films)
    await es_write_data(bulk_query)

    body, status = await make_get_request(f'/{test_id}', {})

    assert status == expected_answer['status']
    if film_id == 'valid_id':
        assert expected_answer['has_title'] == ('title' in body)
        assert body['title'] == 'The Super Start 0'


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'sort': '-imdb_rating', 'page_size': 30, 'page_number': 1}, {'status': 200, 'length': 30}),
        ({'genre': 'valid_genre_id', 'page_size': 50, 'page_number': 1}, {'status': 200, 'length': 1}),
        ({'page_size': 15, 'page_number': 1}, {'status': 200, 'length': 15}),
        ({'page_size': 15, 'page_number': 2}, {'status': 200, 'length': 15}),
        ({'page_size': 50, 'page_number': 3}, {'status': 404, 'length': 1}),
    ]
)
async def test_films_list(generate_film_data, make_bulk_query, make_get_request, es_write_data, query_data, expected_answer):
    valid_genre_id = str(uuid.uuid4())

    films = generate_film_data(31, 'Film')

    if query_data.get('genre') == 'valid_genre_id':
        films[0]['genres'][0]['id'] = valid_genre_id
        query_data['genre'] = valid_genre_id
    
    bulk_query = make_bulk_query(films)
    await es_write_data(bulk_query)
    
    body, status = await make_get_request('', query_data)
    
    assert status == expected_answer['status']
    assert len(body) == expected_answer['length']
    
    if expected_answer['length'] > 1 and query_data.get('sort'):
        ratings = [film['imdb_rating'] for film in body]
        if query_data.get('sort') == '-imdb_rating':
            assert ratings == sorted(ratings, reverse=True)
        elif query_data.get('sort') == 'imdb_rating':
            assert ratings == sorted(ratings)
        

@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'sort': '-imdb_rating', 'page_size': 20, 'page_number': 1}, {'status': 200, 'length': 20}),
        ({'sort': 'imdb_rating', 'page_size': 25, 'page_number': 1}, {'status': 200, 'length': 25}),
        ({'sort': '-imdb_rating', 'page_size': 50}, {'status': 200, 'length': 50}),
    ]
)
async def test_films_sorting(generate_film_data, make_bulk_query, make_get_request, es_write_data, query_data, expected_answer):
    ratings = [5.0 + i*0.1 for i in range(50)]
    films = generate_film_data(50, 'Film Sort', ratings)
    
    bulk_query = make_bulk_query(films)
    await es_write_data(bulk_query)
    
    body, status = await make_get_request('', query_data)
    
    assert status == expected_answer['status']
    assert len(body) == expected_answer['length']
    
    ratings_result = [film['imdb_rating'] for film in body]
    if query_data.get('sort') == '-imdb_rating':
        assert ratings_result == sorted(ratings_result, reverse=True)
    elif query_data.get('sort') == 'imdb_rating':
        assert ratings_result == sorted(ratings_result)