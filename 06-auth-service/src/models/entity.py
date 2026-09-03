import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey, Uuid
from werkzeug.security import check_password_hash, generate_password_hash

from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default="user", nullable=False)

    def __init__(
        self, login: str, password: str, first_name: str, last_name: str, **kw: Any
    ) -> None:
        super().__init__(**kw)
        self.login = login
        self.password = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def __repr__(self) -> str:
        return f"<User {self.login}>"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)


class Roles(str, Enum):
    ADMIN = "admin"
    SUBSCRIBER = "subscriber"
    USER = "member"
