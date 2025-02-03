import os
import sqlite3
import telebot
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telebot.types import BotCommand
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

# Get bot token
API_TOKEN = os.getenv("TELEBOT_API_TOKEN")
DEVELOPMENT = os.getenv("DEVELOPMENT", "True").lower() == "true"
PRODUCTION_URL = os.getenv("PRODUCTION_URL")

if not API_TOKEN:
    raise ValueError("No TELEBOT_API_TOKEN found in .env file")

bot = telebot.TeleBot(API_TOKEN)
app = FastAPI()

# SQLite Database File
DB_FILE = "users.db"

# Initialize ngrok if enabled
if DEVELOPMENT:
    from pyngrok import ngrok
    public_url = ngrok.connect(8000).public_url
    print(f"🌍 ngrok is enabled. Public URL: {public_url}")
else:
    public_url = PRODUCTION_URL

WEBHOOK_URL = f"{public_url}/cm_tg_bot/webhook"


# Database Initialization
def init_db():
    """Creates the users table if it doesn't exist (one row per user)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            memory TEXT
        )
    """)
    conn.commit()
    conn.close()


def store_user_memory(user_id, memory_dump):
    """Stores or updates a user's memory in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, memory) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET memory=excluded.memory
    """, (user_id, memory_dump))
    conn.commit()
    conn.close()


def get_user_memory(user_id):
    """Retrieves the last stored memory for a user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT memory FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


init_db()  # Ensure the database is initialized


@app.get("/")
def home():
    return {"message": "Bot is running with FastAPI & Webhooks!"}


@app.post("/cm_tg_bot/webhook")
async def webhook(request: Request):
    """Handles incoming updates from Telegram via webhook"""
    update = await request.json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return {"status": "ok"}


def set_bot_commands():
    """Sets the Telegram menu buttons"""
    commands = [
        BotCommand("create_post", "📝 Create a New Post")
    ]
    bot.set_my_commands(commands)


set_bot_commands()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏰ Time to OPERATE")


def process_with_ai(chat_id, user_message):
    """Handles processing messages with the AI agent."""
    print(f"🤖 Processing AI request: {user_message}")

    # Fetch user memory
    user_memory = get_user_memory(chat_id)

    # Initialize AI agent
    user_agent = BaseAgent(community_manager_agent_config)

    if user_memory is not None:
        user_agent.memory.load(user_memory)  # Load memory
        print(f"🔄 Memory loaded for user {chat_id}")

    # Run AI agent
    try:
        reply = user_agent.run(BaseAgentInputSchema(chat_message=user_message))
        print("✅ AI Agent executed successfully")
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"❌ Error processing AI agent: {e}")
        bot_reply = (
            "I'm having trouble processing your request. ",
            "Please try again later."
        )

    # Send AI-generated reply
    bot.send_message(chat_id, bot_reply)

    # Store updated memory
    memory_dump = user_agent.memory.dump()
    store_user_memory(chat_id, memory_dump)
    print(f"💾 Memory stored for user {chat_id}")

    # Reset agent memory
    user_agent.memory = AgentMemory(max_messages=20)


@bot.message_handler(commands=['create_post'])
def handle_create_post(message):
    """Handles 'Create Post' button click by triggering AI directly."""
    process_with_ai(message.chat.id, "Craft a new X post")


@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    """Handles user messages and sends them to AI agent."""
    process_with_ai(message.chat.id, message.text)


def set_webhook():
    """Registers the webhook with Telegram"""
    bot.remove_webhook()  # Ensure no old webhooks are active
    success = bot.set_webhook(url=WEBHOOK_URL)
    if success:
        print(f"✅ Webhook set successfully: {WEBHOOK_URL}")
    else:
        print("❌ Failed to set webhook")


if __name__ == "__main__":
    set_webhook()  # Set webhook when the bot starts
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
