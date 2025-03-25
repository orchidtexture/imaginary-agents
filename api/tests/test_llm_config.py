import pytest
from httpx import AsyncClient

import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


async def test_retrieve_empty_llm_configs(client_test: AsyncClient):
    response = await client_test.get("api/v1/llm/config/list")
    assert response.status_code == 200
    msg = response.json()
    assert "llm_configs" in msg and msg["llm_configs"] == []


async def test_retrieve_populated_llm_configs(
    client_test: AsyncClient,
    sample_llm_configs
):
    """Test retrieving populated list of LLM configs"""
    response = await client_test.get("api/v1/llm/config/list")
    assert response.status_code == 200
    msg = response.json()
    assert "llm_configs" in msg
    assert len(msg["llm_configs"]) == 2

    # Verify config data if needed
    config_names = [config["model"] for config in msg["llm_configs"]]
    assert "deepseek-chat" in config_names
    assert "claude-3-opus" in config_names


async def test_create_llm_config_succesfully(client_test: AsyncClient):
    """Test create new LLM Config succesfully"""

    new_config = {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "provider": "deepseek"
    }
    response = await client_test.post("api/v1/llm/config/create", json=new_config)
    assert response.status_code == 200

    # Verify the response contains the created config
    created_config = response.json()
    assert created_config["model"] == "deepseek-chat"
    assert created_config["base_url"] == "https://api.deepseek.com"
    assert created_config["provider"] == "deepseek"

    # Check that it was actually added to the database
    list_response = await client_test.get("api/v1/llm/config/list")
    configs = list_response.json()["llm_configs"]

    # Should now have 1 config in db
    assert len(configs) == 1

    # Check if our new config is in the list
    new_config_exists = False
    for config in configs:
        if config["model"] == "deepseek-chat" and config["provider"] == "deepseek":
            new_config_exists = True
            break

    assert new_config_exists, "Newly created config not found in the list"
