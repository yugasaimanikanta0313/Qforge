"""
QForge — Ollama Local LLM Client
Wraps the ollama-python SDK for async, local model inference.
All calls stay within the on-premises perimeter — zero cloud egress.
"""
import asyncio
import logging
from typing import AsyncIterator, Any
import ollama
from backend.services.llm.base import BaseLLMClient
from backend.config import settings

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Async wrapper around the Ollama Python SDK."""

    def __init__(self, model: str | None = None, host: str | None = None, timeout: float = 60.0):
        self.model = model or settings.ollama_generator_model
        self.host = host or settings.ollama_base_url
        self.timeout = timeout
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Send a generation request to the local Ollama server with timeout.
        Runs in thread pool to prevent blocking asyncio loop.
        """
        logger.debug(f"[OLLAMA] Generating with model={self.model}, prompt_len={len(prompt)}")
        loop = asyncio.get_event_loop()

        def _call():
            resp = self._client.generate(model=self.model, prompt=prompt, **kwargs)
            return resp.response

        try:
            return await asyncio.wait_for(loop.run_in_executor(None, _call), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.error(f"[OLLAMA] Generation timed out after {self.timeout}s for model {self.model}")
            raise TimeoutError(f"Ollama generation timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"[OLLAMA] Generation failed for model={self.model}: {e}")
            raise

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream token chunks asynchronously from Ollama."""
        loop = asyncio.get_event_loop()

        def _get_stream():
            return self._client.generate(model=self.model, prompt=prompt, stream=True, **kwargs)

        stream_gen = await loop.run_in_executor(None, _get_stream)
        for chunk in stream_gen:
            token = chunk.get("response", "")
            if token:
                yield token

    async def ping(self) -> bool:
        """Check if Ollama server is reachable and model is available."""
        try:
            loop = asyncio.get_event_loop()
            models = await asyncio.wait_for(
                loop.run_in_executor(None, self._client.list),
                timeout=5.0
            )
            available = [m.model for m in models.models]
            logger.info(f"[OLLAMA] Available models: {available}")
            return self.model in available or any(self.model in m for m in available)
        except Exception as e:
            logger.warning(f"[OLLAMA] Ping failed: {e}")
            return False
