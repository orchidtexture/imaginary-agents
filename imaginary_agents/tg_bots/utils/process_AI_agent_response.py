import json
import os
from imaginary_agents.helpers.encription_helper import (
    decrypt_secret,
    encrypt_secret
)
import telebot
from imaginary_agents.agents.chatbot_agent import ChatbotAgent
from dotenv import load_dotenv
from imaginary_agents.tg_bots.db import (
    bot_registry_collection,
    bot_users_collection
)
from atomic_agents.agents.base_agent import (
    BaseAgentInputSchema,
    # AgentMemory
)

load_dotenv()

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")


def process_AI_agent_response(bot: telebot.TeleBot, chat_id, user_message):
    """Handles AI-based message processing."""

    # # Determine bot_id by either fetching directly from the DB in
    # # development or using in-memory config
    # # (the latter would be managed by bot_manager)
    # if os.getenv("DEVELOPMENT", "false").lower() in ("true", "1", "yes"):
    #     # In development mode, query the DB directly.
    #     config_doc = bot_registry_collection.find_one({"token": bot.token})
    #     bot_id = config_doc.get("_id") if config_doc else None
    #     logger.info(
    #         f"Fetched bot_id from DB in development mode: {bot_id}"
    #     )
    # else:
    #     from imaginary_agents.tg_bots.bot_manager_v2 import bot_manager
    #     # Attempt to get bot_id from in-memory registry first.
    #     bot_config = bot_manager.bot_configs.get(bot.token, {})
    #     bot_id = bot_config.get("bot_id")
    #     if not bot_id:
    #         # Fallback to querying the DB if bot_id is not found in memory.
    #         config_doc = bot_registry_collection.find_one(
    #             {"token": bot.token}
    #         )
    #         bot_id = config_doc.get("_id") if config_doc else None

    # Initialize AI agent, possibly passing bot_memory if desired.
    user_agent = ChatbotAgent(
        background=bot.background,
        steps=bot.steps,
        output_instructions=bot.output_instructions,
        llm_api_key=bot.llm_api_key,
        llm_provider=bot.llm_provider,
        model=bot.model
    )

    # Run AI agent
    try:
        config_doc = bot_registry_collection.find_one({"token": bot.token})
        bot_id = config_doc.get("_id") if config_doc else None

        bot_memory = retrieve_agent_memory(user_agent, chat_id, bot_id)

        if bot_memory is not None:
            user_agent.memory.load(bot_memory)
            print(f"Memory loaded for user {chat_id}")

        print("running agent")
        reply = user_agent.run(
            BaseAgentInputSchema(chat_message=user_message)
        )
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"AI Error: {e}")
        bot_reply = (
            "I'm having trouble processing your request. ",
            "Please try again later."
        )

    return {"reply": bot_reply, "user_agent": user_agent, "bot_id": bot_id}


def retrieve_agent_memory(user_agent: ChatbotAgent, chat_id, bot_id):
    """Retrieves the agent memory from the database."""

    # Fetch bot_memory from the bot_users collection for this user
    record = bot_users_collection.find_one({
        "bot_id": bot_id,
        "telegram_user_id": chat_id
    })
    key = record.get("encryption_key")
    memory = record.get("bot_memory")
    if memory is None:
        return None
    bot_memories = decrypt_secret(key, memory)
    return json.loads(bot_memories)


def agent_memory_update(user_agent: ChatbotAgent, chat_id, bot_id):
    """Updates the agent memory in the database."""

    # Store updated memory
    memory_dump = user_agent.memory.dump()

    # Gets user's key and encrypts the memory
    key = get_user_key(user_agent, chat_id, bot_id)
    json_str = json.dumps(memory_dump)
    memory = encrypt_secret(key, json_str)

    # Update the bot_memory in the database for this user
    bot_users_collection.update_one(
        {"bot_id": bot_id, "telegram_user_id": chat_id},
        {"$set": {"bot_memory": memory}},
        upsert=True
    )

    # # Reset agent memory for future interactions
    # user_agent.memory = AgentMemory(max_messages=20)


def get_user_key(user_agent: ChatbotAgent, chat_id, bot_id):
    """Gets the user's key in the database."""

    # Gets user encryption key
    user = bot_users_collection.find_one(
        {"bot_id": bot_id, "telegram_user_id": chat_id},
        {"encryption_key"}
    )
    key = user["encryption_key"]
    return key if user and user["encryption_key"] else None
