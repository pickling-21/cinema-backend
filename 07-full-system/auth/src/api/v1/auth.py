from fastapi import APIRouter, Depends, HTTPException, status, Request
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.schemas.auth import TokenResponse, LoginRequest
from src.schemas.entity import UserCreate, UserInDB
from src.services.auth import AuthService, get_auth_service

router = APIRouter()
auth_dep = AuthJWTBearer()
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_user(
    request: Request,
    user_create: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserInDB:
    try:
        return await service.signup(user_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: LoginRequest,
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.login(form_data.login, form_data.password, authorize)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.refresh(authorize)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def logout(
    request: Request,
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout(authorize)
    return None
