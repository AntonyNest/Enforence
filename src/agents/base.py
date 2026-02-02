"""
Базовий клас для CrewAI агентів ENFORENCE.
"""

from typing import Any

from src.llm.router import LLMRouter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """
    Базовий клас для всіх спеціалізованих агентів.

    Надає спільну функціональність:
    - Доступ до LLM роутера
    - Логування
    - Обробка помилок
    """

    name: str = "base_agent"
    description: str = "Базовий агент"
    role: str = "assistant"

    def __init__(self, llm_router: LLMRouter | None = None) -> None:
        self.llm_router = llm_router or LLMRouter()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Виконання задачі агента.

        Args:
            **kwargs: Параметри задачі.

        Returns:
            Результат виконання.
        """
        logger.info(
            "agent_execution_started",
            agent=self.name,
        )
        try:
            result = await self._process(**kwargs)
            logger.info(
                "agent_execution_complete",
                agent=self.name,
            )
            return result
        except Exception as e:
            logger.error(
                "agent_execution_failed",
                agent=self.name,
                error=str(e),
            )
            raise

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Внутрішня логіка агента. Має бути перевизначена в підкласах.

        Args:
            **kwargs: Параметри задачі.

        Returns:
            Результат обробки.
        """
        raise NotImplementedError(f"Агент {self.name} повинен реалізувати _process()")

    def _build_system_prompt(self) -> str:
        """Побудова системного промпту для агента."""
        return (
            f"Ти — {self.role}. {self.description}. "
            "Відповідай виключно українською мовою. "
            "Дотримуйся структури КМУ Постанова №205."
        )
