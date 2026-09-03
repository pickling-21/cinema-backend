import uuid
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from elasticsearch.helpers import async_bulk
import pytest
import aiohttp
import pytest_asyncio
from functional.settings import test_settings


@pytest_asyncio.fixture()
async def es_client():
    client = AsyncElasticsearch(hosts=[test_settings.es_host], verify_certs=False)
    yield client
    await client.close()
    
@pytest_asyncio.fixture()
async def redis_client():
    client = Redis(host=test_settings.redis_host, port=test_settings.redis_port, decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture()
def es_write_data(es_client, redis_client: Redis):
    
    async def inner(data: list[dict]):
        if await es_client.indices.exists(index=test_settings.es_index):
            await es_client.indices.delete(index=test_settings.es_index)

        await redis_client.flushall()
        await es_client.indices.create(
            index=test_settings.es_index,
            **test_settings.es_index_mapping,
        )
        _, errors = await async_bulk(client=es_client, actions=data)
        
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')
        
        await es_client.indices.refresh(index=test_settings.es_index)
        
    return inner


@pytest_asyncio.fixture()
def make_get_request():
    
    async def inner(endpoint: str, query_data: dict[str, str]):
        
        async with aiohttp.ClientSession() as session:
            
            url = f"{test_settings.service_url}/api/v1/films{endpoint}/"
            params = dict(query_data)
            
            async with session.get(url, params=params) as resp:
                body = await resp.text()
                if resp != 500:
                    json_body = await resp.json()
                    return json_body, resp.status
            
    return inner


@pytest.fixture()
def generate_film_data():
    
    def _generate(count=1, title_prefix='The Star', ratings=None):
        if ratings is None:
            ratings = [8.5] * count
            
        films = []
        for i in range(count):
            film = {
                'id': str(uuid.uuid4()),
                'imdb_rating': ratings[i] if i < len(ratings) else 8.5,
                'genres_names': ['Action', 'Sci-Fi'],
                'genres': [
                    {'id': str(uuid.uuid4()), 'name': 'Action'},
                    {'id': str(uuid.uuid4()), 'name': 'Sci-Fi'},
                ],
                'title': f'{title_prefix} {i}',
                'description': 'New World',
                'directors_names': ['Stan'],
                'directors': [
                    {'id': str(uuid.uuid4()), 'name': 'Stan'}
                ],
                'actors_names': ['Ann', 'Bob'],
                'actors': [
                    {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95', 'name': 'Ann'},
                    {'id': 'fb111f22-121e-44a7-b78f-b19191810fbf', 'name': 'Bob'}
                ],
                'writers_names': ['Ben', 'Howard'],
                'writers': [
                    {'id': 'caf76c67-c0fe-477e-8766-3ab3ff2574b5', 'name': 'Ben'},
                    {'id': 'b45bd7bc-2e16-46d5-b125-983d356768c6', 'name': 'Howard'}
                ],
            }
            films.append(film)
        
        return films
    
    return _generate


@pytest.fixture()
def make_bulk_query():

    def _make(es_data: dict):
        bulk_query: list[dict] = []
        for row in es_data:
            data = {'_index': test_settings.es_index, '_id': row['id']}
            data.update({'_source': row})
            bulk_query.append(data)
        return bulk_query
    
    return _make
