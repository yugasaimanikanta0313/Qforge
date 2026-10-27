"""
QForge — Offline FAISS Index Builder Utility
Ingests enterprise guidelines from data/guidelines/, generates BGE-small embeddings,
and serializes the FAISS index and metadata for zero-latency startup.

Usage:
    python -m backend.services.vector_store.index_builder
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import settings
from backend.services.vector_store.faiss_store import FaissVectorStore
from backend.core.logging import get_logger

logger = get_logger(__name__)


def build_and_serialize_index(
    guidelines_dir: str = "data/guidelines",
    index_path: str = "data/faiss_index/guidelines.index",
    metadata_path: str = "data/faiss_index/chunk_metadata.json",
):
    """Build FAISS index and serialize it to the target paths."""
    print(f"Building FAISS index from {guidelines_dir}...")
    store = FaissVectorStore(embedding_model=settings.embedding_model)
    store.build_from_directory(guidelines_dir)
    store.save(index_path, metadata_path)
    print(f"Successfully saved index to {index_path} and metadata to {metadata_path} [OK]")


if __name__ == "__main__":
    build_and_serialize_index(
        guidelines_dir="data/guidelines",
        index_path=settings.faiss_index_path,
        metadata_path=settings.faiss_metadata_path,
    )
