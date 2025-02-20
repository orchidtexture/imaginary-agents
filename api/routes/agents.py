import asyncio
import os
import time
import subprocess
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Literal
import logging
from imaginary_agents.agents.simple_agent import SimpleAgent
from imaginary_agents.agents.chatbot_agent import ChatbotAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agents"])

load_dotenv()

# API Key setup temporary, this should come from database
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or "
        "in the environment variable OPENAI_API_KEY."
    )


class SchemaField(BaseModel):
    type: str  # Type name as string ("str", "int", etc.)
    description: str

    def get_python_type(self) -> type:
        """Convert string type name to Python type."""
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list
        }
        return type_mapping.get(self.type, str)
        # default to str if type not found


class AgentRunRequest(BaseModel):
    type: Literal["simple", "telegram"]
    input_schema_fields: Dict[str, SchemaField] | None = None
    output_schema_fields: Dict[str, SchemaField] | None = None
    background: List[str]
    steps: List[str]
    output_instructions: List[str]
    input_data: Dict[str, Any] | None = None

    @validator('input_data')
    def validate_input_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError("input_data must be a dictionary")
        return v


@router.post("/run")
async def run_agent(config: AgentRunRequest):
    try:
        logger.info(f"Initializing agent of type: {config.type}")

        if config.type == "simple":
            if not config.input_schema_fields or not config.output_schema_fields or not config.input_data:
                raise ValueError("Simple agent requires input and output schema and input_data fields")

            # Convert schema fields to the format SimpleAgent expects
            input_fields = {
                name: {
                    "type": field.get_python_type(),
                    "description": field.description
                }
                for name, field in config.input_schema_fields.items()
            }
            output_fields = {
                name: {
                    "type": field.get_python_type(),
                    "description": field.description
                }
                for name, field in config.output_schema_fields.items()
            }

            agent = SimpleAgent(
                input_schema_fields=input_fields,
                output_schema_fields=output_fields,
                background=config.background,
                steps=config.steps,
                output_instructions=config.output_instructions,
                api_key=API_KEY
            )

            # Validate input data against dynamic schema
            try:
                input_instance = agent.input_schema(**config.input_data)
            except Exception as e:
                raise ValueError(f"Invalid input data: {str(e)}")

            response = agent.run(input_instance)
            return response.dict()
        elif config.type == "telegram":
            logger.info("Launching Telegram bot...")
            
            # Create an environment dict with the current env vars plus any needed additions
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Ensure Python output is unbuffered
            
            try:
                # Open a subprocess with stdout/stderr redirected
                bot_process = subprocess.Popen(
                    ["python3", "imaginary_agents/tg_bots/telegram_agent_bot.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=env
                )
                
                # Start async log monitoring
                async def monitor_output():
                    while True:
                        # Check stdout
                        stdout_line = bot_process.stdout.readline()
                        if stdout_line:
                            logger.info(f"[BOT] {stdout_line.strip()}")
                        
                        # Check stderr
                        stderr_line = bot_process.stderr.readline()
                        if stderr_line:
                            logger.error(f"[ERROR] {stderr_line.strip()}")
                        
                        # Check if process is still running
                        if bot_process.poll() is not None:
                            if bot_process.returncode != 0:
                                logger.error("Bot process terminated with error")
                                raise HTTPException(
                                    status_code=500,
                                    detail="Telegram bot failed to start"
                                )
                            break

                        await asyncio.sleep(0.1)

                # Start monitoring in background
                asyncio.create_task(monitor_output())

                # Return success response immediately
                return {
                    "status": "success",
                    "message": "Telegram bot started",
                    "pid": bot_process.pid
                }

            except Exception as e:
                logger.error(f"Failed to start Telegram bot: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start Telegram bot: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Agent type '{config.type}' not implemented"
            )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
