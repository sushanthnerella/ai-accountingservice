import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_workflow(async_client: AsyncClient):
    # 1. Register User
    reg_payload = {
        "email": "priya.ca@example.com",
        "password": "SecurePassword123!",
        "full_name": "CA Priya Sharma",
        "phone": "+919876543210"
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["email"] == "priya.ca@example.com"
    assert data["full_name"] == "CA Priya Sharma"

    # Duplicate registration should fail
    dup_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 2. Login
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "priya.ca@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    assert access_token is not None

    # 3. Access Protected Route /auth/me
    me_res = await async_client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "priya.ca@example.com"

    # 4. Token Refresh
    refresh_res = await async_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()["data"]
