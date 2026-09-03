"""
CRUD
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    login: str
    password: str
    first_name: str
    last_name: str


class UserInDB(BaseModel):
    id: UUID
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)
