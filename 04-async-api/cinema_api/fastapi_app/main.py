from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from src.api.v1 import films
from src.core import config
from src.db import elastic, redis

app = FastAPI(
    title="Read-only API для онлайн-кинотеатра",
    description="Информация о фильмах, жанрах и людях, участвовавших в создании произведения",
    version="1.0.0",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)

@app.get("/")
async def root():
    return {"message": "Cinema API is running!"}


@app.on_event('startup')
async def startup():
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    elastic.es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_SCHEME}://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])

@app.on_event('shutdown')
async def shutdown():
    await redis.redis.close()
    await elastic.es.close()



app.include_router(films.router, prefix='/api/v1/films', tags=['films'])