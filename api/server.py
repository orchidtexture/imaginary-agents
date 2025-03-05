import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import agents, tg_bots
from imaginary_agents.tg_bots.bot_manager import bot_manager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Imaginary Agents API",
    description="API for interacting with various AI agents",
    version="1.0.0"
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
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tg_bots.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize bot manager when the API starts"""
    # The bot_manager is already initialized when imported
    # You could add any additional startup logic here
    logger.info(f"Bot Manager object: {bot_manager}")
    logger.info("Bot Manager initialized and ready to serve requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when API shuts down"""
    # Add any cleanup code here, if needed
    logger.info("Shutting down Bot Manager")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
