"""
Абстрактний інтерфейс для LLM провайдерів.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Відповідь від LLM провайдера."""

    text: str
    provider: str
    model: str
    tokens_used: int = 0
    duration_ms: float = 0.0


class BaseLLMClient(ABC):
    """
    Абстрактний базовий клас для LLM клієнтів.

    Всі LLM провайдери (MamayLM, Claude) мають реалізувати цей інтерфейс.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Генерація тексту від LLM.

        Args:
            prompt: Основний промпт.
            system_prompt: Системний промпт (опціонально).
            temperature: Температура генерації (0.0-1.0).
            max_tokens: Максимальна кількість токенів відповіді.

        Returns:
            LLMResponse з текстом відповіді та метаданими.

        Raises:
            LLMError: Помилка генерації.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Перевірка доступності LLM провайдера.

        Returns:
            True якщо провайдер доступний.
        """
        ...
