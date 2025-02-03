import os
import sqlite3
import telebot
from fastapi import FastAPI, Request
from dotenv import load_dotenv
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
    """Stores or updates a user's memory in the database
         (overwrites each time)."""
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


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⏰ Time to OPERATE")


@bot.message_handler(func=lambda message: True)
def reply_handler(message):
    """Handles user messages with persistent memory per user."""
    print("📩 New message received")
    chat_id = message.chat.id
    user_message = message.text

    # Fetch the last memory dump for this user
    user_memory = get_user_memory(chat_id)

    # Initialize a fresh agent for this user
    user_agent = BaseAgent(community_manager_agent_config)

    if user_memory is not None:
        user_agent.memory.load(user_memory)  # Load user-specific memory
        print(f"🔄 Memory loaded for user {chat_id}")

    # Attempt to process the user's message
    try:
        reply = user_agent.run(
            BaseAgentInputSchema(chat_message=user_message)
        )
        print("✅ Agent run successful")
        bot_reply = reply.chat_message
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        bot_reply = (
            "I'm having trouble processing your request. ",
            "Please try again later."
        )

    # Send the reply (fallback message if an error occurs)
    bot.reply_to(message, bot_reply)

    # Store the bot's response and updated memory (overwriting previous memory)
    memory_dump = user_agent.memory.dump()
    store_user_memory(chat_id, memory_dump)
    print(f"💾 Memory stored for user {chat_id}")

    # Reset the memory AFTER storing it (prepares for next interaction)
    user_agent.memory = AgentMemory(max_messages=20)


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
