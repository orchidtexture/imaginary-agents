import pytest
from fastapi import status
from httpx import AsyncClient

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


# async def test_retrieve_empty_llm_configs(client_test: AsyncClient):
#     response = await client_test.get("api/v1/llm/config/list")
#     assert response.status_code == 200
#     msg = response.json()
#     assert "llm_configs" in msg and msg["llm_configs"] == []


# async def test_retrieve_populated_llm_configs(
#     client_test: AsyncClient,
#     sample_llm_configs
# ):
#     """Test retrieving populated list of LLM configs"""
#     response = await client_test.get("api/v1/llm/config/list")
#     assert response.status_code == 200
#     msg = response.json()
#     assert "llm_configs" in msg
#     assert len(msg["llm_configs"]) == 2

#     # Verify config data if needed
#     config_names = [config["model"] for config in msg["llm_configs"]]
#     assert "deepseek-chat" in config_names
#     assert "claude-3-opus" in config_names


async def test_create_agent_succesfully(client_test: AsyncClient):
    """Test create new Agent succesfully"""

    new_agent = {
        "name": "Mini Daniel",
        "llm_model": "deepseek-chat",
        "background": [
            "You are an experienced technical project manager",
            "You excel at organizing complex product requirements and tasks",
            "You document everything for developing secure products"
        ],
        "steps": [
            "Analyze the provided notes from a technical meeting",
            "Classify and organize the topics",
            "Create a summary to understand the decisions made in that meeting"
        ],
        "output_instructions": [
            "You thrive on technical environments",
            "You can create simple, comprehensive summaries"
        ],
        "input_schema_fields": {
            "notes": {
                "type": "str",
                "description": "The notes from the technical meeting"
            }
        },
        "output_schema_fields": {
            "summary": {
                "type": "str",
                "description": "The summary of the technical meeting"
            }
        }
    }
    response = await client_test.post(
        "api/v1/agents/orchestrator/create",
        json=new_agent
    )
    assert response.status_code == 200

    # Verify the response contains the created agent
    created_agent = response.json()
    assert created_agent["name"] == "Mini Daniel"

    # # Check that it was actually added to the database
    # list_response = await client_test.get("api/v1/agents/list")
    # agents = list_response.json()["agents"]

    # # Should now have 1 agent in db
    # assert len(agents) == 1

    # # Check if our new agent is in the list
    # new_agent_exists = False
    # for agent in agents:
    #     if agent["llm_model"] == "deepseek-chat" and agent["name"] == "Mini Daniel":
    #         new_agent_exists = True
    #         break

    # assert new_agent_exists, "Newly created agent not found in the list"


async def test_run_agent_with_wrong_input_fields(
    client_test: AsyncClient,
    override_dependencies,
    sample_user,
    sample_agent,
    sample_llm_configs
):
    """Test running an Agent succesfully"""
    response = await client_test.post(
        "api/v1/agents/run",
        json={
            "id": str(sample_agent.id),
            "input_fields": {
                "some_field": "Wrong data"
            }
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
