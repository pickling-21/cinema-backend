from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from src.api.v1 import films
from src.core.config import settings
from src.db import elastic, redis
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
    redis.auth_redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1)
    elastic.es = AsyncElasticsearch(
        hosts=[f"{settings.ELASTIC_SCHEME}://{settings.ELASTIC_HOST}:{settings.ELASTIC_PORT}"]
    )

    yield

    await redis.redis.close()
    await redis.auth_redis.close()
    await elastic.es.close()
    

app = FastAPI(
    title="Read-only API для онлайн-кинотеатра",
    description="Информация о фильмах, жанрах и людях, участвовавших в создании произведения",
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    redirect_slashes=False,
)


@app.get("/")
async def root():
    return {"message": "Cinema API is running!"}


app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
