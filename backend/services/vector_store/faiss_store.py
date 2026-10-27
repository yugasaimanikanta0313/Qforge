"""
QForge — FAISS In-Memory Vector Store Service
Loads enterprise guideline documents, embeds them with BGE-small,
and serves Top-K similarity search for the RAG pipeline.

Key design decisions:
- BGE-small runs entirely on-premises (no cloud API call for embedding)
- FAISS index is rebuilt at startup from the guidelines/ directory or loaded from disk
- Index is cached in memory for sub-millisecond retrieval
"""
import os
import json
import logging
from pathlib import Path
from typing import List
import numpy as np

from backend.services.vector_store.base import BaseVectorStore

logger = logging.getLogger(__name__)

# Lazy imports to avoid slow startup if not used immediately
_sentence_transformers = None
_faiss = None


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


def _get_encoder():
    global _sentence_transformers
    if _sentence_transformers is None:
        from sentence_transformers import SentenceTransformer
        _sentence_transformers = SentenceTransformer
    return _sentence_transformers


class FaissVectorStore(BaseVectorStore):
    """
    In-memory FAISS vector store for enterprise guidelines.
    Thread-safe for read operations (search).
    """

    def __init__(self, embedding_model: str = "BAAI/bge-small-en-v1.5"):
        self.embedding_model_name = embedding_model
        self._encoder = None
        self._index = None
        self._chunks: List[str] = []
        self._is_loaded = False

    def _load_encoder(self):
        if self._encoder is None:
            logger.info(f"[FAISS] Loading embedding model: {self.embedding_model_name}")
            EncoderClass = _get_encoder()
            self._encoder = EncoderClass(self.embedding_model_name)
            logger.info("[FAISS] Embedding model loaded")

    def build_from_directory(self, guidelines_dir: str) -> None:
        """
        Build FAISS index by reading all .md and .txt files in guidelines_dir.
        Chunks each document and embeds with BGE-small — entirely local.
        """
        self._load_encoder()
        faiss = _get_faiss()

        guidelines_path = Path(guidelines_dir)
        if not guidelines_path.exists():
            logger.warning(f"[FAISS] Guidelines directory not found: {guidelines_dir}")
            self._bootstrap_demo_chunks()
            return

        all_chunks = []
        for file in guidelines_path.rglob("*.md"):
            text = file.read_text(encoding="utf-8", errors="ignore")
            chunks = self._chunk_text(text, chunk_size=400, overlap=50)
            all_chunks.extend(chunks)
            logger.info(f"[FAISS] Indexed {len(chunks)} chunks from {file.name}")

        for file in guidelines_path.rglob("*.txt"):
            text = file.read_text(encoding="utf-8", errors="ignore")
            chunks = self._chunk_text(text, chunk_size=400, overlap=50)
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning("[FAISS] No guideline files found — using demo chunks")
            self._bootstrap_demo_chunks()
            return

        self._build_index(all_chunks, faiss)

    def _bootstrap_demo_chunks(self):
        """
        Fallback: loads hardcoded enterprise guideline chunks for demo purposes
        when no guideline files are found on disk.
        """
        faiss = _get_faiss()
        demo_chunks = [
            "Python test functions must be prefixed with test_ and use descriptive names.",
            "Each test must be independent and not rely on shared mutable state between tests.",
            "SQL assertion queries must use COUNT(*) or EXCEPT comparisons to validate row counts.",
            "All pytest tests must include at least one boundary value test (empty input, None, max value).",
            "Test imports should be at the top of the file. Use pytest.mark.parametrize for repetitive cases.",
            "SQL tests must validate both the happy path and cases with NULL values in join columns.",
            "Python functions should be tested with: valid input, empty input, None input, and edge values.",
            "Generated test suites must not have hard-coded database credentials or connection strings.",
            "Use assert statements with descriptive error messages: assert result == expected, 'message'",
            "SQL ETL tests must verify row counts before and after transformation steps.",
        ]
        self._build_index(demo_chunks, faiss)
        logger.info("[FAISS] Bootstrapped with demo enterprise guideline chunks")

    def _build_index(self, chunks: List[str], faiss_module) -> None:
        """Embed chunks and build FAISS flat index."""
        self._chunks = chunks
        logger.info(f"[FAISS] Embedding {len(chunks)} chunks with BGE-small...")
        embeddings = self._encoder.encode(
            chunks,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        embeddings = np.array(embeddings, dtype=np.float32)
        dim = embeddings.shape[1]
        self._index = faiss_module.IndexFlatIP(dim)  # Inner product on normalized = cosine similarity
        self._index.add(embeddings)
        self._is_loaded = True
        logger.info(f"[FAISS] Index built: {self._index.ntotal} vectors, dim={dim}")

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Embed query locally and retrieve Top-K most similar guideline chunks.
        The query string NEVER leaves the local machine — BGE-small runs on-device.
        """
        if not self._is_loaded or self._index is None:
            logger.warning("[FAISS] Index not loaded — returning empty results")
            return []

        self._load_encoder()
        query_vec = self._encoder.encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )
        query_vec = np.array(query_vec, dtype=np.float32)

        k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(query_vec, k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self._chunks):
                results.append(self._chunks[idx])

        logger.debug(f"[FAISS] Query returned {len(results)} chunks")
        return results

    def save(self, index_path: str, metadata_path: str) -> None:
        """Serialize index and metadata to disk."""
        if not self._is_loaded or self._index is None:
            raise ValueError("Cannot save uninitialized index")
        faiss = _get_faiss()
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        faiss.write_index(self._index, index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"[FAISS] Saved index to {index_path} and metadata to {metadata_path}")

    def load(self, index_path: str, metadata_path: str) -> None:
        """Load serialized index and metadata from disk."""
        if not (os.path.exists(index_path) and os.path.exists(metadata_path)):
            raise FileNotFoundError(f"FAISS index or metadata missing: {index_path}, {metadata_path}")
        faiss = _get_faiss()
        self._load_encoder()
        self._index = faiss.read_index(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            self._chunks = json.load(f)
        self._is_loaded = True
        logger.info(f"[FAISS] Loaded index from {index_path} with {len(self._chunks)} chunks")

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """Split text into overlapping word-level chunks."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            start += chunk_size - overlap
        return [c for c in chunks if len(c.strip()) > 20]
