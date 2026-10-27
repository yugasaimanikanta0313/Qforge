"""
QForge — MongoDB Async Client (Motor)
Provides a singleton Motor async client instance used across all DB repositories.
Connection string and DB name come from environment settings only.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db() -> None:
    """
    Initialize the MongoDB Motor client.
    Called once during FastAPI lifespan startup.
    """
    global _client, _db
    logger.info("[DB] Connecting to MongoDB...")
    _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    _db = _client[settings.mongodb_db_name]
    # Ping to verify connection
    await _client.admin.command("ping")
    logger.info(f"[DB] Connected to MongoDB — database: {settings.mongodb_db_name}")


async def close_db() -> None:
    """Close the MongoDB connection. Called on FastAPI lifespan shutdown."""
    global _client
    if _client:
        _client.close()
        logger.info("[DB] MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Dependency-injectable getter for the active database handle."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db
