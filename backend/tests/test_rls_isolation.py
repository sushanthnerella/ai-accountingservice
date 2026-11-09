import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_isolation_and_cross_access(async_client: AsyncClient):
    # Register Org A Owner
    await async_client.post("/api/v1/auth/register", json={
        "email": "owner_a@orga.com",
        "password": "Password123!",
        "full_name": "Owner A"
    })
    token_a = (await async_client.post("/api/v1/auth/login", json={
        "email": "owner_a@orga.com",
        "password": "Password123!"
    })).json()["data"]["access_token"]

    org_a = (await async_client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Org A", "slug": "org-a", "org_type": "FREELANCER"}
    )).json()["data"]["id"]

    # Register Org B Owner
    await async_client.post("/api/v1/auth/register", json={
        "email": "owner_b@orgb.com",
        "password": "Password123!",
        "full_name": "Owner B"
    })
    token_b = (await async_client.post("/api/v1/auth/login", json={
        "email": "owner_b@orgb.com",
        "password": "Password123!"
    })).json()["data"]["access_token"]

    # Org B user attempts to access Org A via header
    cross_res = await async_client.get(
        "/api/v1/clients",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Organization-Id": org_a
        }
    )
    assert cross_res.status_code == 403
    assert cross_res.json()["detail"]["error_code"] == "FORBIDDEN_TENANT_ACCESS"
