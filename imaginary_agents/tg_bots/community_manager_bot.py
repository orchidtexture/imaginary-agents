import os
import telebot
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telebot.types import BotCommand
from imaginary_agents.database.chatbot_db import chatbot_db
from atomic_agents.agents.base_agent import (
    BaseAgentInputSchema,
    BaseAgent,
    AgentMemory
)
from imaginary_agents.agents.community_manager_agent import (
    community_manager_agent_config
)

# Load environment variables
load_dotenv()

# Define encryption password and platform user details
IMAGINARY_AGENTS_API_KEY = os.getenv("IMAGINARY_AGENTS_API_KEY")

# Bot token
# TODO: Retrieve from database is set when bot is created
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Encrypt bot token
ENCRYPTED_BOT_TOKEN = chatbot_db.encrypt_bot_token(
    BOT_TOKEN,
    IMAGINARY_AGENTS_API_KEY
)

# Register the platform user in MongoDB (if not already registered)
# TODO: create a user service to abstract from here
USER_ID = chatbot_db.register_user(IMAGINARY_AGENTS_API_KEY)

# Register or retrieve the chatbot ID
# TODO: create a chatbot service to abstract from here
CHATBOT_ID = chatbot_db.register_chatbot(
    bot_name="community_manager_bot",  # TODO: set by user
    platform="telegram",
    owner_id=USER_ID,
    encrypted_token=ENCRYPTED_BOT_TOKEN
)

# Retrieve bot token securely from DB
SECURE_BOT_TOKEN = chatbot_db.get_bot_token(
    CHATBOT_ID,
    IMAGINARY_AGENTS_API_KEY
)

# Initialize bot
bot = telebot.TeleBot(SECURE_BOT_TOKEN)
app = FastAPI()

DEVELOPMENT = os.getenv("DEVELOPMENT", "True").lower() == "true"
PRODUCTION_URL = os.getenv("PRODUCTION_URL")

# Initialize ngrok if enabled
if DEVELOPMENT:
    from pyngrok import ngrok
    public_url = ngrok.connect(8000).public_url
    print(f"🌍 ngrok is enabled. Public URL: {public_url}")
else:
    public_url = PRODUCTION_URL

WEBHOOK_URL = f"{public_url}/cm_tg_bot/webhook"


# **🔹 FastAPI Routes (Webhook)**
@app.get("/")
def home():
    return {"message": "Bot is running with FastAPI & Webhooks!"}


@app.post("/cm_tg_bot/webhook")   # TODO: add chatbot_id for multiple users
async def webhook(request: Request):
    """Handles incoming updates from Telegram via webhook."""
    update = await request.json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return {"status": "ok"}


# **🔹 Telegram Bot Commands**
def set_bot_commands():
    """Sets Telegram menu buttons."""
    commands = [
        BotCommand("create_post", "📝 Create a New Post"),
        BotCommand("delete_memory", "🗑 Delete Memory")
    ]
    bot.set_my_commands(commands)


set_bot_commands()


# **🔹 Message Handlers**
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
        Welcomes the user when they start the bot and
         registers them in the database.
    """
    chat_id = message.chat.id
    bot.send_message(chat_id, "Welcome to the Community Manager Agent! 🤖")

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
    bot.send_message(message.chat.id, "🗑 Chat memory has been deleted.")


@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    """Handles user messages and sends them to AI agent."""
    process_with_ai(message.chat.id, message.text)


# **🔹 AI Processing Function**
def process_with_ai(chat_id, user_message):
    """Handles AI-based message processing."""
    print(f"🤖 Processing AI request: {user_message}")

    # Fetch stored user memory
    user_memory = chatbot_db.get_user_memory(chat_id)

    # Initialize AI agent
    user_agent = BaseAgent(community_manager_agent_config)

    if user_memory is not None:
        user_agent.memory.load(user_memory)  # Load previous memory
        print(f"🔄 Memory loaded for user {chat_id}")

    # Run AI agent
    try:
        reply = user_agent.run(BaseAgentInputSchema(chat_message=user_message))
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"❌ AI Error: {e}")
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


# **🔹 Webhook Setup & Bot Start**
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
