"""
QForge — Conversational History & Codebase Memory Repository
Stores chat turns, user prompts, prompt iterations, and past analysis summaries in MongoDB.
Enables retrieval of past sessions (like ChatGPT history) and RAG over previous reviews.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
COLLECTION = "conversation_history"


async def save_turn(
    db: AsyncIOMotorDatabase,
    session_id: str,
    user_prompt: str,
    language: str,
    generated_suite: str,
    validation_status: str,
    repair_cycles: int,
    model_used: str,
    repo_context: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> dict:
    """Saves a conversation turn / codebase generation run."""
    doc = {
        "session_id": session_id,
        "language": language,
        "user_prompt": user_prompt,
        "generated_suite": generated_suite,
        "validation_status": validation_status,
        "repair_cycles": repair_cycles,
        "model_used": model_used,
        "repo_context": repo_context or "",
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc),
    }
    await db[COLLECTION].insert_one(doc)
    return doc


async def get_recent_history(
    db: AsyncIOMotorDatabase, limit: int = 50
) -> List[Dict[str, Any]]:
    """Returns recent prompt history across all sessions (for sidebar/history drawer)."""
    cursor = db[COLLECTION].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_session_history(
    db: AsyncIOMotorDatabase, session_id: str
) -> List[Dict[str, Any]]:
    """Retrieves full conversation turns for a given session."""
    cursor = db[COLLECTION].find({"session_id": session_id}, {"_id": 0}).sort("created_at", 1)
    return await cursor.to_list(length=100)


async def search_past_context(
    db: AsyncIOMotorDatabase, keyword: str, limit: int = 3
) -> List[str]:
    """
    Retrieves previous relevant test suites and prompts to inject as RAG context.
    """
    try:
        # Regex search on user_prompt or repo_context
        query = {
            "$or": [
                {"user_prompt": {"$regex": keyword, "$options": "i"}},
                {"repo_context": {"$regex": keyword, "$options": "i"}},
            ],
            "validation_status": "PASS",
        }
        cursor = db[COLLECTION].find(query, {"_id": 0, "generated_suite": 1, "language": 1}).limit(limit)
        docs = await cursor.to_list(length=limit)
        snippets = []
        for d in docs:
            snippet = f"# Past Validated Test ({d.get('language')}):\n{d.get('generated_suite', '')[:600]}..."
            snippets.append(snippet)
        return snippets
    except Exception as e:
        logger.warning(f"[CHAT_REPO] Failed to search past context: {e}")
        return []
