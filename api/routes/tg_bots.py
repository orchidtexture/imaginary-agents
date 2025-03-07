from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
import logging
from imaginary_agents.tg_bots.bot_manager import bot_manager
from imaginary_agents.helpers.encription_helper import generate_user_encryption_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots/telegram", tags=["Telegram Bots"])


class BotStartRequest(BaseModel):
    # agent_id: str
    token: str
    llm_api_key: str
    agent_name: str
    background: List[str]
    steps: List[str]
    output_instructions: List[str]


@router.post("/start_bot/{agent_id}")
def start_bot(agent_id: str, req: BotStartRequest):
    return bot_manager.start_bot(
        agent_id,
        token=req.token,
        agent_name=req.agent_name,
        background=req.background,
        steps=req.steps,
        output_instructions=req.output_instructions,
        llm_api_key=req.llm_api_key
    )


@router.post("/stop_bot/{agent_id}")
def stop_bot(agent_id: str):
    return bot_manager.stop_bot(agent_id)


@router.get("/list_bots")
def list_bots():
    return bot_manager.list_bots()


@router.get("/get_bot_status/{agent_id}")
def bot_status(agent_id: str):
    return bot_manager.get_bot(agent_id)


@router.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token not in bot_manager.bot_configs:
        raise HTTPException(status_code=404, detail="Bot not found.")
    update = await request.json()
    chat_id = update.get("message", {}).get("chat", {}).get("id")
    if chat_id:
        bot_id = bot_manager.bot_configs[token].get("bot_id")
        if bot_id:
            data = {
                "bot_id": bot_id,
                "telegram_user_id": chat_id,
            }
            user = bot_manager.users_collection.find_one({"bot_id": bot_id, "telegram_user_id": chat_id})
            if user is None or "telegram_user_id" not in user:
                data["encryption_key"] = generate_user_encryption_key().decode()
            bot_manager.users_collection.update_one(
                {"bot_id": bot_id, "telegram_user_id": chat_id},
                {"$set": data},
                upsert=True
            )
    bot_instance = bot_manager.get_bot_instance(token)
    bot_instance.process_webhook(update)
    return {"status": "ok"}


@router.get("/bot_details/{token}")
def bot_details(token: str):
    if token not in bot_manager.bot_configs:
        raise HTTPException(status_code=404, detail="Bot not found.")
    bot_instance = bot_manager.get_bot_instance(token)
    webhook_url = bot_manager.get_webhook_url(token)
    return {
        "token": token[:8],
        "isRunning": True,  # If bot exists in bot_configs, it is running
        "webhook_url": webhook_url,
        "agent_name": bot_instance.agent_name,
        "background": bot_instance.background,
        "steps": bot_instance.steps,
        "output_instructions": bot_instance.output_instructions,
    }
