"""
QForge — Google Gemini Cloud LLM Client
Called ONLY when complexity_score >= threshold AND egress policy approves.
Uses the current google-genai SDK (google.genai) with the API key from environment settings.
"""
import asyncio
import logging
from typing import AsyncIterator, Any
from google import genai
from google.genai import types
from backend.services.llm.base import BaseLLMClient
from backend.config import settings

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Async wrapper around the Google Gen AI SDK (google.genai)."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model_name = model or settings.gemini_model
        self.api_key = api_key or settings.gemini_api_key
        self._client = genai.Client(api_key=self.api_key)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Send a generation request to the Gemini cloud API.
        The synchronous SDK call is offloaded to a thread pool executor.
        """
        logger.info(f"[GEMINI] Sending request to {self.model_name} — prompt_len={len(prompt)}")
        loop = asyncio.get_event_loop()

        def _call():
            config = types.GenerateContentConfig(
                temperature=kwargs.get("temperature", 0.2),
                max_output_tokens=kwargs.get("max_output_tokens", 8192),
            )
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text or ""

        try:
            result = await loop.run_in_executor(None, _call)
            logger.info(f"[GEMINI] Response received — output_len={len(result)}")
            return result
        except Exception as e:
            logger.error(f"[GEMINI] API call failed: {e}")
            raise

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream token chunks asynchronously from Gemini."""
        logger.info(f"[GEMINI] Streaming request to {self.model_name}")
        loop = asyncio.get_event_loop()

        def _get_stream():
            config = types.GenerateContentConfig(
                temperature=kwargs.get("temperature", 0.2),
                max_output_tokens=kwargs.get("max_output_tokens", 8192),
            )
            return self._client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

        stream_iter = await loop.run_in_executor(None, _get_stream)
        for chunk in stream_iter:
            if chunk.text:
                yield chunk.text

    async def ping(self) -> bool:
        """Verify API key validity by testing generation."""
        try:
            await self.generate("ping", max_output_tokens=5)
            return True
        except Exception as e:
            logger.warning(f"[GEMINI] Ping failed: {e}")
            return False
