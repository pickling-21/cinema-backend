"""Unit tests for src.core.auth: every branch of get_current_user."""
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.core.auth import AuthPayload, get_current_user, get_optional_user
from fakes import make_token


def creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.fixture
def redis_mock() -> AsyncMock:
    mock = AsyncMock()
    mock.exists.return_value = 0
    return mock


async def test_missing_header_is_rejected(redis_mock):
    with pytest.raises(HTTPException) as err:
        await get_current_user(None, redis_mock)
    assert err.value.status_code == 401
    assert err.value.detail == "Authorization header required"
    assert err.value.headers == {"WWW-Authenticate": "Bearer"}
    redis_mock.exists.assert_not_awaited()


async def test_valid_token_returns_payload(redis_mock):
    user = await get_current_user(creds(make_token("42", "admin", "abc")), redis_mock)
    assert isinstance(user, AuthPayload)
    assert (user.user_id, user.role, user.jti) == ("42", "admin", "abc")
    redis_mock.exists.assert_awaited_once_with("blacklist:abc")


async def test_expired_token_is_rejected(redis_mock):
    with pytest.raises(HTTPException) as err:
        await get_current_user(creds(make_token(exp_delta=-10)), redis_mock)
    assert (err.value.status_code, err.value.detail) == (401, "Token has expired")


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        make_token(secret="another-secret"),
        make_token(algorithm="HS512"),
    ],
    ids=["garbage", "wrong-signature", "wrong-algorithm"],
)
async def test_invalid_token_is_rejected(redis_mock, token):
    with pytest.raises(HTTPException) as err:
        await get_current_user(creds(token), redis_mock)
    assert (err.value.status_code, err.value.detail) == (401, "Invalid token")
    redis_mock.exists.assert_not_awaited()


async def test_token_without_jti_is_rejected(redis_mock):
    with pytest.raises(HTTPException) as err:
        await get_current_user(creds(make_token(jti=None)), redis_mock)
    assert (err.value.status_code, err.value.detail) == (401, "Token missing jti claim")


async def test_revoked_token_is_rejected(redis_mock):
    redis_mock.exists.return_value = 1
    with pytest.raises(HTTPException) as err:
        await get_current_user(creds(make_token(jti="gone")), redis_mock)
    assert (err.value.status_code, err.value.detail) == (401, "Token has been revoked")
    redis_mock.exists.assert_awaited_once_with("blacklist:gone")


async def test_role_defaults_to_user(redis_mock):
    user = await get_current_user(creds(make_token(role=None)), redis_mock)
    assert user.role == "user"


@pytest.mark.xfail(
    strict=True,
    reason="auth.py turns a missing 'sub' claim into the string 'None' instead of rejecting the token",
)
async def test_token_without_sub_is_rejected(redis_mock):
    with pytest.raises(HTTPException):
        await get_current_user(creds(make_token(sub=None)), redis_mock)


async def test_optional_user_without_header_is_none(redis_mock):
    assert await get_optional_user(None, redis_mock) is None


async def test_optional_user_with_header_delegates(redis_mock):
    user = await get_optional_user(creds(make_token("7", jti="x")), redis_mock)
    assert (user.user_id, user.jti) == ("7", "x")
