from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
import logging
from api.models import Agent, User

from api.auth import current_user

from database.database import (
    add_agent,
    retrieve_user_by_email,
    retrieve_agent,
    retrieve_llm_config_by_model,
    update_user_data
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentRunRequest(BaseModel):
    """Request model for running an Agent"""
    id: str = Field(..., description="Agent ID")
    input_message: Optional[str] = Field(
        default=None,
        description="The user's input message to be analyzed and responded to."
    )
    input_fields: Optional[Dict[str, str]] = Field(
        default=None,
        description="Input fields for the agent"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "67e31ddb8ff9fd95480077e9",
                "input_message": "Go to duckduck.go and search for 'how to make a cake'",
                "input_fields": {
                    "input_message": "Tell me all the possible evolutions of eevee"
                }
            }
        }
    )


@router.post("/run")
async def run_agent(
    config: AgentRunRequest,
    user: User = Depends(current_user)
):
    try:
        # Retrieve Agent from DB
        agent = await retrieve_agent(config.id)
        logger.info(f"Running agent: {agent.name}")
        # fetch llm_config from db by model name
        llm_config = await retrieve_llm_config_by_model(model=agent.llm_model)
        # fetch user from db by email
        logger.info(f"User: {user}")
        user = await retrieve_user_by_email(user.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        llm_api_key = user.llm_api_keys[llm_config.provider]

        try:
            response = await agent.run(
                llm_api_key=llm_api_key,
                input_message=config.input_message,
                input_fields=config.input_fields,
            )
        except Exception as e:
            if isinstance(e, ValueError):
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            raise HTTPException(
                status_code=status_code,
                detail=f"Error running agent: {str(e)}"
            )
        return response

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if isinstance(e, HTTPException):
            raise HTTPException(status_code=e.status_code, detail=str(e))
        else:
            logger.error("it is not http exception")
            raise HTTPException(status_code=500, detail=str(e))


class CreateAgentRequest(BaseModel):
    """Request model for creating an Agent"""

    name: str = Field(..., description="Name of the agent")
    llm_model: str = Field(..., description="The identifier of the model to use")
    type: str = Field(
        default="simple",
        description="Type of agent (e.g., orchestrator, simple)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the agent"
    )
    background: Optional[List[str]] = Field(
        default=None,
        description="Background context for the agent"
    )
    steps: Optional[List[str]] = Field(
        default=None,
        description="Steps the agent follows"
    )
    output_instructions: Optional[List[str]] = Field(
        default=None,
        description="Instructions for output formatting"
    )
    input_schema_fields: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Input schema field definitions"
    )
    output_schema_fields: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description="Output schema field definitions"
    )
    tg_bot_token: Optional[str] = Field(
        default=None,
        description="Telegram bot token if applicable"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Mini Daniel",
                "llm_model": "deepseek-chat",
                "type": "simple",
                "description": "A simple agent for summarizing technical meetings",
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
                },
                "tg_bot_token": "some_token"
            }
        }
    )


@router.post("/create")
async def create_agent(config: CreateAgentRequest, user: User = Depends(current_user)):
    """
    Create a new Agent
    :return: The newly created Agent
    """
    try:
        # Convert request model to Agent and save it
        # Model dump bc request model has same fields as Agent model
        new_agent = Agent(**config.model_dump())
        res = await add_agent(new_agent)

        # Add agent to user
        current_user_agents = user.agents
        new_agents = current_user_agents + [new_agent]
        await update_user_data(id=user.id, data={"agents": new_agents})

        return res
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
