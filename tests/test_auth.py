import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_users: dict):
    # Retrieve credentials
    payload = {
        "username": "test_user_2",
        "password": "password123"
    }
    response = await client.post("/auth/login", data=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    payload = {
        "username": "non_existent",
        "password": "wrong_password"
    }
    response = await client.post("/auth/login", data=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_users: dict):
    token = test_users["user_2"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["username"] == "test_user_2"
    assert json_data["is_active"] is True

@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_users_authenticated(client: AsyncClient, test_users: dict):
    # Any authenticated token can view all users
    token = test_users["user_2"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/users", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
