import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    users,
    agents,
    tg_bots,
    crawler_agent,
    browser_use,
    orchestrator_agent,
    llm_configs
)
from imaginary_agents.tg_bots.bot_manager import bot_manager

from config import init_db, close_db_connection
from api.models import LLMConfig, Agent

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Load environment variables
FIEF_BASE_URL = os.getenv("FIEF_BASE_URL")
FIEF_CLIENT_ID = os.getenv("FIEF_CLIENT_ID")
FIEF_CLIENT_SECRET = os.getenv("FIEF_CLIENT_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The bot_manager is already initialized when imported
    # You could add any additional startup logic here
    logger.info(f"Bot Manager object: {bot_manager}")
    logger.info("Bot Manager initialized and ready to serve requests")

    # Initialize the database
    await init_db([LLMConfig, Agent])
    logger.info("Database initialized successfully")

    yield
    # Add any cleanup code here, if needed
    logger.info("Shutting down Bot Manager")
    await close_db_connection()
    logger.info("Database connection closed")

app = FastAPI(
    title="Imaginary Agents API",
    description="API for interacting with various AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tg_bots.router, prefix="/api/v1")
app.include_router(crawler_agent.router, prefix="/api/v1")
app.include_router(browser_use.router, prefix="/api/v1")
app.include_router(orchestrator_agent.router, prefix="/api/v1")
app.include_router(llm_configs.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
