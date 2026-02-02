"""
Клієнт для Anthropic Claude API.

Claude використовується для compliance checking та як fallback для MamayLM.
"""

import time

import httpx

from src.config import settings
from src.llm.base import BaseLLMClient, LLMResponse
from src.utils.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class ClaudeClient(BaseLLMClient):
    """
    Клієнт для Anthropic Claude API.

    Використовується для:
    - Compliance checking (основна задача)
    - Fallback генерації якщо MamayLM недоступний
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Генерація тексту через Claude API.

        Args:
            prompt: Текст промпту.
            system_prompt: Системний промпт.
            temperature: Температура генерації.
            max_tokens: Ліміт токенів.

        Returns:
            LLMResponse з текстом відповіді.

        Raises:
            LLMError: Якщо API недоступний або помилка автентифікації.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        payload: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.monotonic()

        try:
            response = await self.client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            duration_ms = (time.monotonic() - start_time) * 1000
            text = data["content"][0]["text"]
            input_tokens = data.get("usage", {}).get("input_tokens", 0)
            output_tokens = data.get("usage", {}).get("output_tokens", 0)

            logger.info(
                "claude_generation_complete",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=round(duration_ms, 2),
            )

            return LLMResponse(
                text=text,
                provider="claude",
                model=self.model,
                tokens_used=input_tokens + output_tokens,
                duration_ms=duration_ms,
            )

        except httpx.HTTPStatusError as e:
            logger.error("claude_http_error", status=e.response.status_code)
            raise LLMError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                provider="claude",
            ) from e
        except httpx.RequestError as e:
            logger.error("claude_connection_error", error=str(e))
            raise LLMError(
                f"Не вдалося з'єднатися з Claude API: {e}",
                provider="claude",
            ) from e

    async def health_check(self) -> bool:
        """Перевірка доступності Claude API."""
        try:
            # Мінімальний запит для перевірки API key
            response = await self.client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=15.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Закриття HTTP клієнта."""
        await self.client.aclose()
