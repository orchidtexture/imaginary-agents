import os
from typing import Optional, List, Type
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from dotenv import load_dotenv

load_dotenv()

# Global client and database references
_client: Optional[AsyncIOMotorClient] = None
_db = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """
    Get the MongoDB client instance (creates it if it doesn't exist)

    Returns:
        AsyncIOMotorClient: The Motor MongoDB client
    """
    global _client
    if _client is None:
        uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
        _client = AsyncIOMotorClient(uri, appname="imaginary.agents")
    return _client


async def get_database():
    """
    Get the MongoDB database instance

    Returns:
        AsyncIOMotorDatabase: The Motor MongoDB database
    """
    client = await get_mongo_client()
    return client['imaginary_agents_api']


async def init_db(document_models: Optional[List[Type[Document]]] = None):
    """
    Initialize the database connection with Beanie ODM

    Args:
        document_models: Optional list of Beanie document models to register
    """
    global _db
    client = await get_mongo_client()
    _db = client['imaginary_agents_api']

    if document_models:
        await init_beanie(database=_db, document_models=document_models)

    return _db


async def close_db_connection():
    """Close the MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None


async def get_collection(collection_name: str):
    """
    Get a specific collection from the database

    Args:
        collection_name: Name of the collection to retrieve

    Returns:
        AsyncIOMotorCollection: The requested collection
    """
    if _db is None:
        await get_database()
    return _db[collection_name]
