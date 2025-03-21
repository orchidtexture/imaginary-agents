from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from imaginary_agents.agents.orchestrator import OrchestratorAgent
from imaginary_agents import tools

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
