"""
Розумна маршрутизація між LLM провайдерами.

Стратегія:
- MamayLM: генерація контенту українською (секції 1-10)
- Claude: compliance checking, валідація якості
- Fallback: Claude якщо MamayLM недоступний
"""

from src.config import settings
from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.claude_client import ClaudeClient
from src.llm.mamay_client import MamayLMClient
from src.utils.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Типи задач для маршрутизації
COMPLIANCE_TASKS = {"compliance_check", "quality_validation", "structure_review"}
GENERATION_TASKS = {"section_generation", "content_creation", "requirements_analysis"}


class LLMRouter:
    """
    Маршрутизатор запитів між MamayLM та Claude.

    Розподіляє задачі між провайдерами на основі типу задачі
    з автоматичним fallback на Claude.
    """

    def __init__(
        self,
        mamay_client: MamayLMClient | None = None,
        claude_client: ClaudeClient | None = None,
    ) -> None:
        self.mamay_client = mamay_client or MamayLMClient()
        self.claude_client = claude_client or ClaudeClient()
        self.default_provider = settings.default_llm_provider

    async def route(
        self,
        task_type: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Маршрутизація запиту до відповідного LLM провайдера.

        Args:
            task_type: Тип задачі (compliance_check, section_generation, тощо).
            prompt: Текст промпту.
            system_prompt: Системний промпт.
            temperature: Температура генерації.
            max_tokens: Ліміт токенів.

        Returns:
            LLMResponse від обраного провайдера.

        Raises:
            LLMError: Якщо обидва провайдери недоступні.
        """
        # Compliance задачі завжди через Claude (reasoning capabilities)
        if task_type in COMPLIANCE_TASKS:
            logger.info("routing_to_claude", task_type=task_type)
            return await self.claude_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Генерація контенту — спочатку MamayLM, потім Claude як fallback
        logger.info("routing_to_mamay", task_type=task_type)
        try:
            return await self.mamay_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMError as e:
            logger.warning(
                "mamay_fallback_to_claude",
                task_type=task_type,
                mamay_error=str(e),
            )
            return await self.claude_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

    def get_client(self, provider: str) -> BaseLLMClient:
        """
        Отримання конкретного LLM клієнта.

        Args:
            provider: Назва провайдера ('mamay' або 'claude').

        Returns:
            Екземпляр LLM клієнта.
        """
        if provider == "mamay":
            return self.mamay_client
        elif provider == "claude":
            return self.claude_client
        else:
            raise ValueError(f"Невідомий LLM провайдер: {provider}")

    async def health_check(self) -> dict[str, bool]:
        """Перевірка доступності всіх LLM провайдерів."""
        return {
            "mamay": await self.mamay_client.health_check(),
            "claude": await self.claude_client.health_check(),
        }

    async def close(self) -> None:
        """Закриття всіх HTTP клієнтів."""
        await self.mamay_client.close()
        await self.claude_client.close()
