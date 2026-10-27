"""
QForge — Vector Store Abstraction
Defines the abstract interface for guideline vector indexing and search.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorStore(ABC):
    """Abstract interface for guideline retrieval vector stores."""

    @abstractmethod
    def build_from_directory(self, dir_path: str) -> None:
        """Ingest text/markdown files from directory, chunk, embed, and index."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Perform dense vector similarity search and return top_k chunk texts."""
        pass

    @abstractmethod
    def save(self, index_path: str, metadata_path: str) -> None:
        """Serialize index and metadata to disk."""
        pass

    @abstractmethod
    def load(self, index_path: str, metadata_path: str) -> None:
        """Load serialized index and metadata from disk."""
        pass
