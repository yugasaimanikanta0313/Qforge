"""
QForge — Audit Log Repository
Handles write-optimized append operations for agent execution audit records.
"""
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

COLLECTION = "audit_logs"


async def save_audit_log(db: AsyncIOMotorDatabase, session_id: str, state: dict) -> str:
    """
    Persist a full agent execution audit record to MongoDB.
    Returns the inserted document ID as a string.
    """
    doc = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc),
        "language": state.get("language"),
        "complexity_score": state.get("complexity_score"),
        "routing_path": state.get("routing_path"),
        "validation_status": state.get("validation_status"),
        "repair_cycles_used": state.get("repair_cycle", 0),
        "generation_model_used": state.get("generation_model_used"),
        "validation_errors": state.get("validation_errors", []),
        "audit_notes": state.get("audit_notes", []),
        "ast_fingerprint": state.get("ast_fingerprint", {}),
        "input_length": len(state.get("raw_input", "")),
        "output_length": len(state.get("final_test_suite", "") or ""),
    }
    result = await db[COLLECTION].insert_one(doc)
    logger.info(f"[AUDIT_REPO] Saved audit log for session {session_id}: {result.inserted_id}")
    return str(result.inserted_id)


async def get_audit_logs(db: AsyncIOMotorDatabase, limit: int = 50) -> list[dict]:
    """Retrieve recent audit logs sorted by timestamp descending."""
    cursor = db[COLLECTION].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_session_audit(db: AsyncIOMotorDatabase, session_id: str) -> list[dict]:
    """Retrieve all audit records for a specific session."""
    cursor = db[COLLECTION].find({"session_id": session_id}, {"_id": 0})
    return await cursor.to_list(length=100)
