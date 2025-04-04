import pytest
from httpx import AsyncClient

import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


async def test_retrieve_self_user_unauthorized(client_test: AsyncClient):
    # Test without authentication
    response = await client_test.get("/api/v1/users/self")
    assert response.status_code == 401


async def test_retrieve_self_user(
    client_test: AsyncClient,
    override_dependencies,
    sample_user
):
    response = await client_test.get("/api/v1/users/self")
    assert response.status_code == 200
    msg = response.json()
    assert "email" in msg and msg["email"] == sample_user.email
