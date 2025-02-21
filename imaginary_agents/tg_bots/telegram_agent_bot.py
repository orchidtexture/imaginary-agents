import json
import os
import telebot
import time
import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telebot.types import BotCommand
from telebot.apihelper import ApiTelegramException
from imaginary_agents.database.chatbot_db import chatbot_db
from atomic_agents.agents.base_agent import (
    BaseAgentInputSchema,
    AgentMemory
)
from imaginary_agents.agents.chatbot_agent import ChatbotAgent

# Load environment variables
load_dotenv()

background = json.loads(os.getenv('BACKGROUND', '[]'))
steps = json.loads(os.getenv('STEPS', '[]'))
output_instructions = json.loads(os.getenv('OUTPUT_INSTRUCTIONS', '[]'))
llm_api_key = os.getenv('LLM_API_KEY', '')
encrypted_bot_token = os.getenv('ENCRYPTED_BOT_TOKEN', '')
imaginary_agents_api_key = os.getenv('IMAGINARY_AGENTS_API_KEY', '')
bot_name = os.getenv('AGENT_NAME', '')

DEVELOPMENT = os.getenv("DEVELOPMENT", "True").lower() == "true"
PRODUCTION_URL = os.getenv("PRODUCTION_URL")


# Add this after loading environment variables
def validate_environment():
    """Validate required environment variables."""
    required_vars = {
        'ENCRYPTED_BOT_TOKEN': encrypted_bot_token,
        'IMAGINARY_AGENTS_API_KEY': imaginary_agents_api_key,
        'LLM_API_KEY': llm_api_key,
        'AGENT_NAME': bot_name,
        'BACKGROUND': background,
        'STEPS': steps,
        'OUTPUT_INSTRUCTIONS': output_instructions
    }

    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {
                ', '.join(missing_vars)
            }"
        )

    if not DEVELOPMENT and not PRODUCTION_URL:
        raise ValueError(
            "PRODUCTION_URL must be set when not in development mode"
        )


# Add this right after environment variable loading
validate_environment()

# Register the platform user in MongoDB (if not already registered)
# TODO: create a user service to abstract from here
USER_ID = chatbot_db.register_user(imaginary_agents_api_key)

# Register or retrieve the chatbot ID
# TODO: create a chatbot service to abstract from here
CHATBOT_ID = chatbot_db.register_chatbot(
    bot_name=bot_name,
    platform="telegram",
    owner_id=USER_ID
)

# Retrieve bot token securely from DB
DECRYPTED_BOT_TOKEN = chatbot_db.decrypt_bot_token(
    encrypted_bot_token,
    imaginary_agents_api_key
)

# Initialize bot
bot = telebot.TeleBot(DECRYPTED_BOT_TOKEN)
app = FastAPI()

# Get the first 32 digits of the encrypted token
BOT_TOKEN_DIGITS = encrypted_bot_token[:32] if encrypted_bot_token else ""

# Initialize ngrok if enabled
if DEVELOPMENT:
    from pyngrok import ngrok
    public_url = ngrok.connect(8776).public_url
    print(f"🌍 ngrok is enabled. Public URL: {public_url}")
else:
    public_url = PRODUCTION_URL

WEBHOOK_URL = f"{public_url}/telegram/{BOT_TOKEN_DIGITS}"


# **🔹 FastAPI Routes (Webhook)**
@app.get("/")
def home():
    return {"message": "Bot is running with FastAPI & Webhooks!"}


@app.post("/telegram/{token}")
async def webhook(token: str, request: Request):
    """Handles incoming updates from Telegram via webhook."""
    if token != BOT_TOKEN_DIGITS:
        return {"status": "unauthorized"}

    update = await request.json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return {"status": "ok"}


def set_bot_commands_with_retry(bot, commands, max_retries=3, initial_delay=1):
    """Sets Telegram menu buttons with retry logic."""
    for attempt in range(max_retries):
        try:
            bot.set_my_commands(commands)
            print("Bot commands set successfully")
            return True
        except ApiTelegramException as e:
            if e.error_code == 429:  # Too Many Requests
                retry_after = e.result_json.get(
                    'parameters', {}
                ).get('retry_after', initial_delay * (2 ** attempt))
                print(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                print(f"Telegram API Error: {e}")
                raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    raise RuntimeError("Failed to set bot commands after maximum retries")


# **🔹 Telegram Bot Commands**
def set_bot_commands():
    """Sets Telegram menu buttons."""
    commands = [
        BotCommand("create_post", "📝 Create a New Post"),
        BotCommand("delete_memory", "🗑 Delete Memory")
    ]
    set_bot_commands_with_retry(bot, commands)


set_bot_commands()


# **🔹 Message Handlers**
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
        Welcomes the user when they start the bot and
         registers them in the database.
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, "Welcome to the Chef Agent! 🤖")

    # Step 1: Register chatbot user in MongoDB (if not exists)
    chatbot_user_id = chatbot_db.register_chatbot_user(chat_id, CHATBOT_ID)

    # Step 2: Ensure chatbot user is linked to the chatbot
    chatbot_db.link_chatbot_user(CHATBOT_ID, chatbot_user_id)


@bot.message_handler(commands=['create_post'])
def handle_create_post(message):
    """Triggers AI processing for 'Create Post' command."""
    process_with_ai(message.chat.id, "Craft a new X post")


@bot.message_handler(commands=['delete_memory'])
def delete_memory(message):
    """Deletes stored memory for the user."""
    chatbot_db.delete_user_memory(message.chat.id)
    bot.send_message(message.chat.id, "Chat memory has been deleted.")


@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    """Handles user messages and sends them to AI agent."""
    process_with_ai(message.chat.id, message.text)


# **🔹 AI Processing Function**
def process_with_ai(chat_id, user_message):
    """Handles AI-based message processing."""
    print(f"Processing AI request: {user_message}")

    # Fetch stored user memory
    user_memory = chatbot_db.get_user_memory(chat_id)

    # Initialize AI agent
    user_agent = ChatbotAgent(
        background=background,
        steps=steps,
        output_instructions=output_instructions,
        llm_api_key=llm_api_key
    )

    print(user_agent)

    if user_memory is not None:
        user_agent.memory.load(user_memory)  # Load previous memory
        print(f"Memory loaded for user {chat_id}")

    # Run AI agent
    try:
        print("running agent")
        reply = user_agent.run(BaseAgentInputSchema(chat_message=user_message))
        print("reply generated")
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"AI Error: {e}")
        bot_reply = (
            "I'm having trouble processing your request. ",
            "Please try again later."
        )

    # Send AI-generated reply
    bot.send_message(chat_id, bot_reply)

    # Store updated memory
    memory_dump = user_agent.memory.dump()
    chatbot_db.store_user_memory(chat_id, memory_dump)

    # Reset agent memory for future interactions
    user_agent.memory = AgentMemory(max_messages=20)


# **🔹 Start Bot & Server Function**
def start_bot():
    """Start the bot and FastAPI server."""
    try:
        # Verify bot token is valid
        if not DECRYPTED_BOT_TOKEN:
            raise ValueError("Bot token is not properly decrypted or missing")

        # Test bot connection
        bot_info = bot.get_me()
        print(f"Connected to bot: @{bot_info.username}")

        # Setup webhook
        try:
            setup_webhook_with_retry(bot, WEBHOOK_URL)
        except Exception as webhook_error:
            print(f"Webhook Error: {webhook_error}")
            raise

        # Configure FastAPI
        if not app.routes:
            print("Error: No routes configured in FastAPI app")
            raise ValueError("FastAPI app is not properly configured")

        print("Starting FastAPI server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8776,
            log_level="info",
            access_log=True
        )

    except Exception as e:
        error_msg = f"Bot startup failed: {str(e)}"
        print(error_msg)
        raise RuntimeError(error_msg)


def setup_webhook_with_retry(bot, webhook_url, max_retries=3, initial_delay=1):
    """Setup webhook with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            # Remove existing webhook
            bot.remove_webhook()
            time.sleep(0.5)  # Small delay between remove and set

            # Set new webhook
            bot.set_webhook(url=webhook_url)
            print(f"Webhook set successfully to {webhook_url}")
            return True

        except ApiTelegramException as e:
            if e.error_code == 429:  # Too Many Requests
                retry_after = e.result_json.get(
                    'parameters', {}
                ).get('retry_after', initial_delay * (2 ** attempt))
                print(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                print(f"Telegram API Error: {e}")
                raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    raise RuntimeError("Failed to set webhook after maximum retries")


def run():
    start_bot()


if __name__ == "__main__":
    run()
