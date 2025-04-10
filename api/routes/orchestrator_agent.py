from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
import logging
from imaginary_agents.agents.orchestrator import OrchestratorAgent
from imaginary_agents import tools


from api.models import Agent
from database.database import add_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/orchestrator", tags=["Gigachad Agents"])

registered_tools = [  # TODO: assign dinamically perhaps from db
    {
        "tool": tools.BrowserUseTool,
        "input_schema": tools.BrowserUseToolInputSchema,
        "output_schema": tools.BrowserUseToolOutputSchema,
    },
    {
        "tool": tools.CrawlerTool,
        "input_schema": tools.CrawlerToolInputSchema,
        "output_schema": tools.CrawlerToolOutputSchema,
    }
]


class AgentRunRequest(BaseModel):
    chat_message: str
    agent_name: Optional[str] = None
    llm_api_key: str
    llm_provider: str
    llm_model: str


@router.post("/run")
async def run_agent(config: AgentRunRequest):
    try:
        logger.info("Running orchestrator agent")

        agent = OrchestratorAgent(
            available_tools=registered_tools,  # This comes from db
            api_key=config.llm_api_key,
            llm_provider=config.llm_provider,
            model=config.llm_model
        )

        agent_input = OrchestratorAgent.input_schema(chat_message=config.chat_message)

        response = agent.run(agent_input)
        return response.dict()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class CreateAgentRequest(BaseModel):
    """Request model for creating an Agent"""

    name: str = Field(..., description="Name of the agent")
    llm_model: str = Field(..., description="The identifier of the model to use")
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
async def create_agent(config: CreateAgentRequest):
    """
    Create a new Agent
    :return: The newly created Agent
    """
    try:
        # Convert request model to Agent and save it
        # Model dump bc request model has same fields as Agent model
        new_agent = Agent(**config.model_dump())
        res = await add_agent(new_agent)
        return res
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
