import pytest
from fastapi import status
from httpx import AsyncClient

from database.database import retrieve_agent

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


async def test_create_agent_succesfully(
    client_test: AsyncClient,
    override_dependencies,
):
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
        "api/v1/agents/create",
        json=new_agent
    )
    assert response.status_code == 200

    # Verify the response contains the created agent
    created_agent = response.json()
    assert created_agent["name"] == "Mini Daniel"

    # Check that it was actually added to the database
    agent_from_db = await retrieve_agent(id=created_agent["_id"])
    assert agent_from_db is not None

    # TODO: Check if Agent was successfully linked to User


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
