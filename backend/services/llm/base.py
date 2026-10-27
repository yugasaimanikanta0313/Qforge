"""
QForge — LLM Client Base Abstraction
Defines the standard async interface for LLM backends (Ollama, Gemini, etc.).
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any


class BaseLLMClient(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate full completion text asynchronously."""
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream token chunks asynchronously."""
        pass

    async def ping(self) -> bool:
        """Health check for the LLM service. Defaults to True."""
        return True
