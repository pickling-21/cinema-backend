import uuid
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import pytest
import aiohttp
import pytest_asyncio

import asyncio
from functional.settings import test_settings
pytestmark = pytest.mark.asyncio

@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'query': 'The Star'},
                {'status': 200, 'length': 50}
        ),
        (
                {'query': 'star', 'page_size':60},
                {'status': 200, 'length': 60}
        ),
        (
                {'query': 'star', 'page_size':20, 'page_number':1},
                {'status': 200, 'length': 20}
        ),
        (
                {'query': 'star', 'page_number':3, 'page_size':25},
                {'status': 200, 'length': 10}
        ),
        (
                {'query': 'Mashed potato'},
                {'status': 404, 'length': 1}
        )
    ]
)
async def test_search(generate_film_data, make_bulk_query, make_get_request, es_write_data, query_data, expected_answer):
    """
    Тест поиска по фильмам в Elasticsearch.
    Генерирует данные, загружает их в индекс и проверяет поиск.
    """

    films = generate_film_data(60)

    bulk_query = make_bulk_query(films)
    
    await es_write_data(bulk_query)
    
    body, status = await make_get_request('/search', query_data)
    
    assert status == expected_answer['status']
    assert len(body) == expected_answer['length'] 