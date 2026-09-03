from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import get_session
from src.models.entity import User, Roles
from src.schemas.auth import UserRolesResponse

VALID_ROLES = {r.value for r in Roles}


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant(self, user_id: UUID, role: str) -> UserRolesResponse:
        if role not in VALID_ROLES:
            raise ValueError(f"Недопустимая роль. Допустимые: {VALID_ROLES}")

        user = await self.db.get(User, user_id)
        if not user:
            raise LookupError("Пользователь не найден")

        user.role = role
        await self.db.commit()

        return UserRolesResponse(user_id=user_id, role=user.role)

    async def revoke(self, user_id: UUID, role: str) -> UserRolesResponse:
        user = await self.db.get(User, user_id)
        if not user:
            raise LookupError("Пользователь не найден")

        if user.role != role:
            raise ValueError("У пользователя нет этой роли")

        user.role = Roles.USER.value
        await self.db.commit()

        return UserRolesResponse(user_id=user_id, role=user.role)

    async def check(self, user_id: UUID, role: str) -> bool:
        user = await self.db.get(User, user_id)
        if not user:
            raise LookupError("Пользователь не найден")

        return user.role == role


def get_role_service(db: AsyncSession = Depends(get_session)) -> RoleService:
    return RoleService(db)
