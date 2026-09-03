from fastapi import APIRouter, Depends, HTTPException, status
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer

from src.schemas.auth import TokenResponse, LoginRequest
from src.schemas.entity import UserCreate, UserInDB
from src.services.auth import AuthService, get_auth_service

router = APIRouter()
auth_dep = AuthJWTBearer()


@router.post("/signup", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserInDB:
    try:
        return await service.signup(user_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: LoginRequest,
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.login(form_data.login, form_data.password, authorize)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.refresh(authorize)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    authorize: AuthJWT = Depends(auth_dep),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout(authorize)
    return None
