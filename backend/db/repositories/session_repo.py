"""
QForge — Session Repository
CRUD database operations for session documents.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.db.models.session import SessionModel

logger = logging.getLogger(__name__)

COLLECTION = "sessions"


async def create_session(db: AsyncIOMotorDatabase, session_data: dict) -> dict:
    """Insert a new session document."""
    doc = session_data.copy()
    if "created_at" not in doc:
        doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)

    await db[COLLECTION].update_one(
        {"session_id": doc["session_id"]},
        {"$set": doc},
        upsert=True
    )
    logger.info(f"[SESSION_REPO] Created/updated session {doc['session_id']}")
    return doc


async def get_session(db: AsyncIOMotorDatabase, session_id: str) -> Optional[dict]:
    """Retrieve session by session_id."""
    return await db[COLLECTION].find_one({"session_id": session_id}, {"_id": 0})


async def update_session_status(
    db: AsyncIOMotorDatabase, session_id: str, status: str, metadata: dict | None = None
) -> bool:
    """Update status and optional metadata for a session."""
    update_data: Dict[str, Any] = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if metadata:
        for k, v in metadata.items():
            update_data[f"metadata.{k}"] = v

    result = await db[COLLECTION].update_one(
        {"session_id": session_id},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def list_sessions(db: AsyncIOMotorDatabase, limit: int = 50) -> List[dict]:
    """List recent sessions sorted by creation time descending."""
    cursor = db[COLLECTION].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def delete_session(db: AsyncIOMotorDatabase, session_id: str) -> bool:
    """Delete a session document."""
    result = await db[COLLECTION].delete_one({"session_id": session_id})
    return result.deleted_count > 0
