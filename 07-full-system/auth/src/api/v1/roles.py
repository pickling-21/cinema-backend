from fastapi import APIRouter, Depends, HTTPException, status
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer

from src.db.redis_db import is_blacklisted
from src.models.entity import Roles
from src.schemas.auth import RoleRequest, RoleCheckResponse, UserRolesResponse
from src.services.roles import RoleService, get_role_service

router = APIRouter()
auth_dep = AuthJWTBearer()


async def get_current_user_role(authorize: AuthJWT = Depends(auth_dep)) -> dict:
    """Проверяет access-токен и возвращает user_id и role из JWT claims."""
    await authorize.jwt_required()
    raw_jwt = await authorize.get_raw_jwt()
    jti = raw_jwt["jti"]

    if await is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отозван"
        )

    return {
        "user_id": await authorize.get_jwt_subject(),
        "role": raw_jwt.get("role", "user"),
    }


@router.post("/grant", response_model=UserRolesResponse)
async def grant_role(
    body: RoleRequest,
    current: dict = Depends(get_current_user_role),
    service: RoleService = Depends(get_role_service),
):
    if current["role"] != Roles.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    try:
        return await service.grant(body.user_id, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/revoke", response_model=UserRolesResponse)
async def revoke_role(
    body: RoleRequest,
    current: dict = Depends(get_current_user_role),
    service: RoleService = Depends(get_role_service),
):
    if current["role"] != Roles.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    try:
        return await service.revoke(body.user_id, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/check", response_model=RoleCheckResponse)
async def check_role(
    body: RoleRequest,
    current: dict = Depends(get_current_user_role),
    service: RoleService = Depends(get_role_service),
):
    try:
        has_role = await service.check(body.user_id, body.role)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return RoleCheckResponse(has_role=has_role)
