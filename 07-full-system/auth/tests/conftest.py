import os
import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.db.postgres import get_session
from src.db import redis_db
from src.core.config import settings

_engine = create_async_engine(str(settings.pg_dsn))
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def _override_get_session():
    async with _SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    dsn = str(settings.pg_dsn).replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute("TRUNCATE refresh_tokens, users CASCADE")
    finally:
        await conn.close()
    yield


@pytest_asyncio.fixture(autouse=True)
async def setup_redis():
    from redis.asyncio import Redis

    client = Redis.from_url(str(settings.redis_dsn))
    redis_db.redis = client
    yield client
    await client.flushdb()
    await client.aclose()
    redis_db.redis = None


@pytest_asyncio.fixture()
async def client():
    from src.main import app

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def registered_user(client: AsyncClient) -> dict:
    """Регистрирует пользователя и возвращает данные + креды."""
    creds = {
        "login": "testuser",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }
    resp = await client.post("/api/v1/auth/signup", json=creds)
    assert resp.status_code == 201
    data = resp.json()
    return {**data, "login": creds["login"], "password": creds["password"]}


@pytest_asyncio.fixture()
async def auth_tokens(client: AsyncClient, registered_user: dict) -> dict:
    """Логинит пользователя и возвращает пару токенов."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "login": registered_user["login"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200
    return resp.json()


@pytest_asyncio.fixture()
async def admin_tokens(client: AsyncClient) -> dict:
    """Создаёт суперпользователя через cli и возвращает токены."""
    from src.cli import create_superuser

    login, password = "adminuser", "adminpass123"
    await create_superuser(login, password)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"login": login, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()
