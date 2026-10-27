"""
QForge — Demo script for testing the full agent pipeline from the terminal.
Useful for hackathon demos without needing the React frontend.

Run with:
  python demo_run.py

Make sure your .env file is populated before running.
"""
import asyncio
import json
import uuid
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import settings
from backend.services.vector_store.faiss_store import FaissVectorStore
from backend.core.app_state import set_vector_store
from backend.agents.graph import build_graph
from backend.agents.state import AgentState

# ── Demo payloads for each hackathon phase ─────────────────────────────────────

DEMO_PYTHON_SIMPLE = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""

DEMO_PYTHON_COMPLEX = """
import hashlib
from functools import lru_cache
from typing import Optional

class CacheManager:
    def __init__(self, max_size: int = 1000):
        self._store = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[bytes]:
        hashed = hashlib.sha256(key.encode()).hexdigest()
        if hashed in self._store:
            self._hits += 1
            return self._store[hashed]
        self._misses += 1
        return None

    def set(self, key: str, value: bytes) -> bool:
        if len(self._store) >= self._max_size:
            oldest = next(iter(self._store))
            del self._store[oldest]
        hashed = hashlib.sha256(key.encode()).hexdigest()
        self._store[hashed] = value
        return True

    @lru_cache(maxsize=128)
    def stats(self) -> dict:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._store)}
"""

DEMO_SQL = """
SELECT 
    c.customer_id,
    c.customer_name,
    SUM(o.total_amount) as lifetime_value,
    COUNT(DISTINCT o.order_id) as order_count,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.created_at) as last_order_date
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status IN ('completed', 'shipped')
  AND o.created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
GROUP BY c.customer_id, c.customer_name
HAVING lifetime_value > 1000
ORDER BY lifetime_value DESC
LIMIT 100;
"""


async def run_demo(code: str, language: str, label: str):
    print("\n" + "=" * 70)
    print(f"  DEMO: {label}")
    print("=" * 70)
    print(f"Language: {language.upper()}")
    print(f"Input preview: {code.strip()[:120]}...")
    print("-" * 70)

    session_id = str(uuid.uuid4())[:8]

    initial_state: AgentState = {
        "session_id": session_id,
        "raw_input": code.strip(),
        "language": language,
        "complexity_score": 0,
        "routing_path": "local",
        "ast_fingerprint": {},
        "context_chunks": [],
        "generated_test_suite": "",
        "generation_model_used": "",
        "validation_status": "PENDING",
        "validation_errors": [],
        "repair_cycle": 0,
        "final_test_suite": None,
        "audit_notes": [],
    }

    vector_store = FaissVectorStore(embedding_model=settings.embedding_model)
    vector_store.build_from_directory("data/guidelines")
    set_vector_store(vector_store)

    graph = build_graph(vector_store)
    current_state = dict(initial_state)

    async for event in graph.astream(initial_state, stream_mode="updates"):
        for node_name, output in event.items():
            current_state = {**current_state, **output}
            print(f"\n  ▶ NODE: {node_name.upper()}", flush=True)
            if node_name == "router":
                print(f"    Complexity Score : {output.get('complexity_score')}/10", flush=True)
                print(f"    Routing Path     : {output.get('routing_path', '').upper()}", flush=True)
                print(f"    Language Detected: {output.get('language', '').upper()}", flush=True)
                print(f"    FAISS Chunks     : {len(output.get('context_chunks', []))}", flush=True)
            elif node_name == "generator":
                suite = output.get("generated_test_suite", "")
                print(f"    Model Used       : {output.get('generation_model_used')}", flush=True)
                print(f"    Repair Cycle     : #{output.get('repair_cycle', 0)}", flush=True)
                print(f"    Generated {len(suite)} chars of test code", flush=True)
            elif node_name == "validator":
                status = output.get("validation_status")
                errors = output.get("validation_errors", [])
                repair = output.get("repair_cycle", 0)
                icon = "PASS [OK]" if status == "PASS" else "FAIL [X]"
                print(f"    Status: {icon}", flush=True)
                if errors:
                    print(f"    Errors ({len(errors)}): {errors[0][:80]}...", flush=True)
                    print(f"    -> Routing back to GENERATOR (cycle #{repair})", flush=True)

    # Print final audit trail
    print("\n" + "-" * 70, flush=True)
    print("  AUDIT TRAIL:", flush=True)
    for note in current_state.get("audit_notes", []):
        print(f"    • {note}", flush=True)


async def main():
    print("[QForge] Framework — Demo Runner")
    print("   Testing all three hackathon phases\n")

    # Phase 1: Simple Python → should route LOCAL
    await run_demo(DEMO_PYTHON_SIMPLE, "python", "Phase 1 — Simple Python (LOCAL routing expected)")

    # Phase 2: Complex Python → may route CLOUD
    await run_demo(DEMO_PYTHON_COMPLEX, "python", "Phase 2 — Complex Python (CLOUD routing possible)")

    # Phase 3: SQL Query
    await run_demo(DEMO_SQL, "sql", "Phase 3 — Complex SQL Query")


if __name__ == "__main__":
    asyncio.run(main())
