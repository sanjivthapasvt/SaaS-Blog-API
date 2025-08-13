import pytest


@pytest.mark.asyncio
async def test_health_lifespan(client):
    # test to ensure app starts and dependency overrides are in effect
    resp = await client.get("/docs")
    assert resp.status_code in (200, 404)
