# db/redis_db.py
from typing import Optional
from redis.asyncio import Redis

redis: Optional[Redis] = None


async def get_redis() -> Redis:
    return redis


async def add_to_blacklist(jti: str, ttl_seconds: int) -> None:
    await redis.set(f"blacklist:{jti}", "1", ex=ttl_seconds)


async def is_blacklisted(jti: str) -> bool:
    return await redis.exists(f"blacklist:{jti}")
