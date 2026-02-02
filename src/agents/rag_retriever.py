"""
Агент RAG пошуку.

Знаходить релевантний контекст з бази знань ТЗ для кожної секції.
"""

from typing import Any

from src.agents.base import BaseAgent
from src.rag.retriever import RAGRetriever
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGRetrieverAgent(BaseAgent):
    """
    Агент для пошуку релевантного контексту з бази знань.

    Використовує семантичний пошук по індексованих зразках ТЗ
    для надання контексту при генерації нових секцій.
    """

    name = "rag_retriever"
    description = "Пошук релевантних фрагментів з бази знань ТЗ"
    role = "спеціаліст з пошуку інформації"

    def __init__(
        self,
        retriever: RAGRetriever | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.retriever = retriever or RAGRetriever()

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Пошук контексту для генерації ТЗ.

        Args:
            project_description: Опис проєкту.
            requirements: Структуровані вимоги.
            sections: Список секцій для пошуку (опціонально).

        Returns:
            Словник {section_id: context_text} для кожної секції.
        """
        project_description = kwargs.get("project_description", "")
        requirements = kwargs.get("requirements", {})
        sections = kwargs.get("sections", [str(i) for i in range(1, 11)])

        # Формування пошукового запиту з вимог
        search_query = self._build_search_query(project_description, requirements)

        contexts: dict[str, str] = {}

        for section_id in sections:
            context = await self.retriever.search_for_section(
                section_id=section_id,
                project_description=search_query,
                top_k=3,
            )
            contexts[section_id] = context

        logger.info(
            "rag_contexts_retrieved",
            sections_count=len(contexts),
            non_empty=sum(1 for c in contexts.values() if c),
        )

        return {"contexts": contexts}

    @staticmethod
    def _build_search_query(
        project_description: str,
        requirements: dict[str, Any],
    ) -> str:
        """Побудова пошукового запиту з опису та вимог."""
        parts = [project_description]

        if summary := requirements.get("summary"):
            parts.append(summary)

        if func_reqs := requirements.get("functional_requirements"):
            parts.append("; ".join(func_reqs[:3]))

        return " ".join(parts)
