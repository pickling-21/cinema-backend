"""
Auth flow
"""

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    login: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class RoleRequest(BaseModel):
    user_id: UUID
    role: str = Field(..., min_length=1)


class RoleCheckResponse(BaseModel):
    has_role: bool


class UserRolesResponse(BaseModel):
    user_id: UUID
    role: str
