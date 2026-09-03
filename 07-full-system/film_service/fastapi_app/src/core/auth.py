from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis

from src.core.config import settings
from src.db.redis import get_auth_redis

security = HTTPBearer(auto_error=False)


class AuthPayload:
    def __init__(self, user_id: str, role: str, jti: str):
        self.user_id = user_id
        self.role = role
        self.jti = jti


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    redis: Redis = Depends(get_auth_redis),
) -> AuthPayload:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    jti = payload.get("jti")
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing jti claim",
        )

    # Check Redis blacklist (DB 1, same as auth_service)
    blacklisted = await redis.exists(f"blacklist:{jti}")
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return AuthPayload(
        user_id=str(payload.get("sub")),
        role=payload.get("role", "user"),
        jti=jti,
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    redis: Redis = Depends(get_auth_redis),
) -> Optional[AuthPayload]:
    if credentials is None:
        return None
    return await get_current_user(credentials, redis)
