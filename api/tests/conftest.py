import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

from api.server import app

from api.models import LLMConfig
from config.db import _client, _db


@pytest.fixture()
async def client_test():
    """
    Create an instance of the client.
    :return: yield HTTP client.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac


@pytest.fixture(autouse=True)
async def mock_db_connection():
    """
    Replace the MongoDB connection with a mock for testing.
    This runs automatically for all tests.
    """

    # Save original globals properly
    original_client = _client
    original_db = _db

    # Set up mock client and database
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client.get_database(name="imaginary_agents_test")

    # Override the global variables
    import config.db
    config.db._client = mock_client
    config.db._db = mock_db

    # Initialize Beanie with the mock database
    document_models = [
        LLMConfig,
        # Add other document models here
    ]
    await init_beanie(document_models=document_models, database=mock_db)

    yield mock_db

    # Restore original globals after test
    config.db._client = original_client
    config.db._db = original_db


@pytest.fixture
async def sample_llm_configs():
    """Add sample LLM configs to the mock database."""
    # Create and insert test data
    sample_configs = [
        LLMConfig(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            provider="deepseek"
        ),
        LLMConfig(
            model="claude-3-opus",
            base_url="https://api.anthropic.com",
            provider="https://api.anthropic.com"
        )
    ]

    created_configs = []
    for config in sample_configs:
        created = await config.create()
        created_configs.append(created)

    yield created_configs
