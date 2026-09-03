from httpx import AsyncClient


async def test_signup_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "login": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["first_name"] == "New"


async def test_signup_duplicate_login(client: AsyncClient, registered_user):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "login": registered_user["login"],
            "password": "otherpass",
            "first_name": "Other",
            "last_name": "User",
        },
    )
    assert resp.status_code == 409


async def test_login_success(client: AsyncClient, registered_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "login": registered_user["login"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient, registered_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"login": registered_user["login"], "password": "wrongpass"},
    )
    assert resp.status_code == 401


async def test_refresh_success(client: AsyncClient, auth_tokens):
    resp = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {auth_tokens['refresh_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "refresh_token" in data


async def test_refresh_reuse_token(client: AsyncClient, auth_tokens):
    # Первый refresh шк
    resp1 = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {auth_tokens['refresh_token']}"},
    )
    assert resp1.status_code == 200

    # Повторный refresh падает
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {auth_tokens['refresh_token']}"},
    )
    assert resp2.status_code == 401


async def test_logout_success(client: AsyncClient, auth_tokens):
    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert resp.status_code == 204
