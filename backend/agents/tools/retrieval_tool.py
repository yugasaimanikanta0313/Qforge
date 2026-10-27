"""
QForge — Retrieval Tool
Wraps FAISS similarity search as a callable agent tool for guideline extraction.
"""
from typing import List
from backend.services.vector_store.faiss_store import FaissVectorStore


def retrieve_guidelines(vector_store: FaissVectorStore, query: str, top_k: int = 5) -> List[str]:
    """
    Invokable tool for retrieving enterprise guidelines.
    Performs local dense embedding retrieval without network egress.
    """
    if not vector_store:
        return []
    return vector_store.search(query, top_k=top_k)
