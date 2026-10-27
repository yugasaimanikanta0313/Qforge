"""
QForge — Test Artifact Repository
Database persistence and retrieval for verified test suite artifacts.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.db.models.test_artifact import TestArtifactModel

logger = logging.getLogger(__name__)

COLLECTION = "test_artifacts"


async def save_artifact(db: AsyncIOMotorDatabase, artifact_data: dict) -> str:
    """Insert or update a verified test suite artifact."""
    doc = artifact_data.copy()
    if "created_at" not in doc:
        doc["created_at"] = datetime.now(timezone.utc)

    result = await db[COLLECTION].update_one(
        {"artifact_id": doc["artifact_id"]},
        {"$set": doc},
        upsert=True
    )
    logger.info(f"[ARTIFACT_REPO] Saved artifact {doc['artifact_id']} for session {doc.get('session_id')}")
    return doc["artifact_id"]


async def get_artifact(db: AsyncIOMotorDatabase, artifact_id: str) -> Optional[dict]:
    """Retrieve artifact by artifact_id."""
    return await db[COLLECTION].find_one({"artifact_id": artifact_id}, {"_id": 0})


async def get_session_artifacts(db: AsyncIOMotorDatabase, session_id: str) -> List[dict]:
    """Retrieve all artifacts produced during a specific session."""
    cursor = db[COLLECTION].find({"session_id": session_id}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(length=50)


async def list_artifacts(db: AsyncIOMotorDatabase, limit: int = 50) -> List[dict]:
    """List recent test artifacts."""
    cursor = db[COLLECTION].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
