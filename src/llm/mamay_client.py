"""
Клієнт для MamayLM-Gemma-2-9B на RunPod.

MamayLM — українська мовна модель для генерації контенту ТЗ.
"""

import time

import httpx

from src.config import settings
from src.llm.base import BaseLLMClient, LLMResponse
from src.utils.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MamayLMClient(BaseLLMClient):
    """
    Клієнт для MamayLM на RunPod.

    Використовує OpenAI-сумісний API (vLLM/llama.cpp backend).
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or settings.mamay_llm_url).rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.model_name = "MamayLM-Gemma-2-9B"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Генерація тексту через MamayLM на RunPod.

        Args:
            prompt: Текст промпту українською.
            system_prompt: Системний промпт для контексту.
            temperature: Температура генерації.
            max_tokens: Ліміт токенів відповіді.

        Returns:
            LLMResponse з українським текстом.

        Raises:
            LLMError: Якщо RunPod API недоступний.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.monotonic()

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            duration_ms = (time.monotonic() - start_time) * 1000
            text = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            logger.info(
                "mamay_generation_complete",
                tokens=tokens_used,
                duration_ms=round(duration_ms, 2),
            )

            return LLMResponse(
                text=text,
                provider="mamay",
                model=self.model_name,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
            )

        except httpx.HTTPStatusError as e:
            logger.error("mamay_http_error", status=e.response.status_code)
            raise LLMError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                provider="mamay",
            ) from e
        except httpx.RequestError as e:
            logger.error("mamay_connection_error", error=str(e))
            raise LLMError(
                f"Не вдалося з'єднатися з RunPod: {e}",
                provider="mamay",
            ) from e

    async def health_check(self) -> bool:
        """Перевірка доступності MamayLM на RunPod."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v1/models",
                timeout=10.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Закриття HTTP клієнта."""
        await self.client.aclose()
