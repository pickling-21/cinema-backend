from datetime import datetime, timedelta

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from async_fastapi_jwt_auth import AuthJWT

from src.core.config import settings
from src.db.postgres import get_session
from src.db.redis_db import add_to_blacklist
from src.models.entity import User, RefreshToken
from src.schemas.auth import TokenResponse
from src.schemas.entity import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_login(self, login: str) -> User | None:
        stmt = select(User).where(User.login == login)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_user(self, user_create: UserCreate) -> User:
        # check if login exists
        existed_user = await self.get_user_by_login(user_create.login)
        if existed_user:
            raise ValueError("Пользователь с таким логином уже существует")

        # user creation
        user_dto = jsonable_encoder(user_create)
        user = User(**user_dto)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_token_pair(self, user: User, authorize: AuthJWT) -> TokenResponse:
        # генерируем токен
        access_token = await authorize.create_access_token(
            subject=str(user.id),
            user_claims={"role": user.role},
        )
        refresh_token = await authorize.create_refresh_token(subject=str(user.id))

        raw_refresh = await authorize.get_raw_jwt(refresh_token)
        refresh_jti = raw_refresh["jti"]

        # сохраняем токен в бд, чтобы потом проверить и заблокировать если что
        db_refresh_token = RefreshToken(
            id=refresh_jti,
            user_id=user.id,
            expires_at=datetime.utcnow()
            + timedelta(days=settings.jwt_refresh_expire_days),
        )
        self.db.add(db_refresh_token)
        await self.db.commit()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(self, authorize: AuthJWT) -> TokenResponse:
        # актуален ли токен?
        await authorize.jwt_refresh_token_required()

        # чекаем базу данных
        current_user = await authorize.get_jwt_subject()
        raw_jwt = await authorize.get_raw_jwt()
        token_jti = raw_jwt.get("jti")

        stmt = select(RefreshToken).where(
            RefreshToken.id == token_jti,
            RefreshToken.is_revoked == False,
        )
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise ValueError("Токен недействителен или уже использован")

        db_token.is_revoked = True  # использован

        # получаем роль пользователя для нового токена
        user_result = await self.db.execute(select(User).where(User.id == current_user))
        user = user_result.scalar_one_or_none()

        # выдаем новый токен
        new_access_token = await authorize.create_access_token(
            subject=current_user,
            user_claims={"role": user.role if user else "user"},
        )
        new_refresh_token = await authorize.create_refresh_token(subject=current_user)

        # получаем jti нового refresh токена
        raw_new_refresh = await authorize.get_raw_jwt(new_refresh_token)
        new_refresh_jti = raw_new_refresh["jti"]

        new_db_token = RefreshToken(
            id=new_refresh_jti,
            user_id=current_user,
            expires_at=datetime.utcnow()
            + timedelta(days=settings.jwt_refresh_expire_days),
        )
        self.db.add(new_db_token)
        await self.db.commit()

        return TokenResponse(
            access_token=new_access_token, refresh_token=new_refresh_token
        )

    async def revoke_tokens(self, authorize: AuthJWT) -> None:
        await authorize.jwt_required()

        raw_jwt = await authorize.get_raw_jwt()
        jti = raw_jwt["jti"]
        exp = raw_jwt["exp"]

        # добавляем access-токен в Redis blacklist
        ttl = int(exp - datetime.utcnow().timestamp())
        if ttl > 0:
            await add_to_blacklist(jti, ttl)

        # отзываем все refresh-токены пользователя
        user_id = await authorize.get_jwt_subject()
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def signup(self, user_create: UserCreate) -> User:
        return await self.create_user(user_create)

    async def login(
        self, login: str, password: str, authorize: AuthJWT
    ) -> TokenResponse:
        # существует ли пользователь с таким логином и паролем?
        user = await self.get_user_by_login(login)
        # чек пароля
        if not user or not user.check_password(password):
            raise ValueError("Неверный логин или пароль")
        return await self.create_token_pair(user, authorize)

    async def refresh(self, authorize: AuthJWT) -> TokenResponse:
        return await self.refresh_tokens(authorize)

    async def logout(self, authorize: AuthJWT) -> None:
        await self.revoke_tokens(authorize)


def get_auth_service(db: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(db)
