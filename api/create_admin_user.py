import os
import asyncio
import motor.motor_asyncio
from beanie import init_beanie
from uuid import uuid4
import argparse

# Import your models
from api.models import User, APIKey

from database.database import add_user, add_api_key

from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")


async def create_user(email: str):
    # Connect to MongoDB
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)

    # Initialize Beanie with the document models
    await init_beanie(
        database=client.imaginary_agents_api,  # Use your actual database name
        document_models=[User, APIKey]
    )

    # First create an API key
    api_key = APIKey(
        key=f"sk-{uuid4().hex}"  # Generate a random API key with prefix
    )
    await add_api_key(api_key)  # Save the API key to the database
    print(f"Created API key: {api_key.key}")

    # Create a new user with the API key linked
    new_user = User(
        email=email,
        llm_api_keys={
            "openai": "sk-your-openai-key",
            "anthropic": "sk-your-anthropic-key"
        },
        api_keys=[api_key]  # Link the API key to the user
    )

    # Save the user to the database
    await add_user(new_user)
    print(f"Created user with email: {new_user.email}")
    print(f"User ID: {new_user.id}")

    # Verify we can retrieve the user by API key
    retrieved_user = await User.find(User.api_keys.key == api_key.key).first_or_none()
    if retrieved_user:
        print(f"Successfully retrieved user by API key: {retrieved_user.email}")
    else:
        print("Failed to retrieve user by API key")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Create an admin user with the specified email'
    )
    parser.add_argument(
        '--email',
        type=str,
        required=True,
        help='Email address for the admin user'
    )

    # Parse arguments
    args = parser.parse_args()

    # Run the async function with the provided email
    asyncio.run(create_user(args.email))
