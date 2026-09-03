from httpx import AsyncClient


async def test_grant_success(client: AsyncClient, admin_tokens, registered_user):
    resp = await client.post(
        "/api/v1/roles/grant",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "subscriber"


async def test_grant_forbidden(client: AsyncClient, auth_tokens, registered_user):
    resp = await client.post(
        "/api/v1/roles/grant",
        json={"user_id": registered_user["id"], "role": "admin"},
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert resp.status_code == 403


async def test_grant_invalid_role(client: AsyncClient, admin_tokens, registered_user):
    resp = await client.post(
        "/api/v1/roles/grant",
        json={"user_id": registered_user["id"], "role": "nonexistent"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 400


async def test_revoke_success(client: AsyncClient, admin_tokens, registered_user):
    # Сначала выдаём роль
    await client.post(
        "/api/v1/roles/grant",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    # Потом отзываем
    resp = await client.post(
        "/api/v1/roles/revoke",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "member"


async def test_revoke_role_user_doesnt_have(
    client: AsyncClient, admin_tokens, registered_user
):
    resp = await client.post(
        "/api/v1/roles/revoke",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 400


async def test_check_role_true(client: AsyncClient, admin_tokens, registered_user):
    # Выдаём роль
    await client.post(
        "/api/v1/roles/grant",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    resp = await client.post(
        "/api/v1/roles/check",
        json={"user_id": registered_user["id"], "role": "subscriber"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["has_role"] is True


async def test_check_role_false(client: AsyncClient, admin_tokens, registered_user):
    resp = await client.post(
        "/api/v1/roles/check",
        json={"user_id": registered_user["id"], "role": "admin"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["has_role"] is False
