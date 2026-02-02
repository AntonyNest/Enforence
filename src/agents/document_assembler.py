"""
Агент збірки фінального документу ТЗ.

Об'єднує секції, застосовує результати compliance check,
формує фінальний JSON документ.
"""

from datetime import datetime, timezone
from typing import Any

from src.agents.base import BaseAgent
from src.models.kmu_205 import KMU_205_STRUCTURE
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentAssemblerAgent(BaseAgent):
    """
    Агент для збірки фінального документу ТЗ.

    Об'єднує результати всіх агентів у єдиний документ:
    - Секції від section_generator
    - Оцінки від compliance_checker
    - Метадані проєкту
    """

    name = "document_assembler"
    description = "Збірка та фіналізація документу ТЗ"
    role = "документаліст"

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Збірка фінального документу.

        Args:
            project_id: ID проєкту.
            project_name: Назва проєкту.
            sections: Список згенерованих секцій.
            compliance_result: Результат compliance check.
            requirements: Структуровані вимоги.

        Returns:
            Фінальний документ у форматі JSON.
        """
        project_id = kwargs.get("project_id", "")
        project_name = kwargs.get("project_name", "")
        sections = kwargs.get("sections", [])
        compliance_result = kwargs.get("compliance_result", {})
        requirements = kwargs.get("requirements", {})

        # Впорядкування секцій
        ordered_sections = self._order_sections(sections)

        # Збірка фінального документу
        document = {
            "id": project_id,
            "project_name": project_name,
            "template_type": "kmu_205",
            "sections": ordered_sections,
            "compliance_score": compliance_result.get("compliance_score", 0.0),
            "compliance_details": {
                "missing_sections": compliance_result.get("missing_sections", []),
                "warnings": compliance_result.get("warnings", []),
                "recommendations": compliance_result.get("recommendations", []),
            },
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_sections": len(ordered_sections),
                "requirements_summary": requirements.get("summary", ""),
                "system_type": requirements.get("system_type", ""),
            },
        }

        logger.info(
            "document_assembled",
            project_id=project_id,
            sections_count=len(ordered_sections),
            compliance_score=document["compliance_score"],
        )

        return document

    @staticmethod
    def _order_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Впорядкування секцій за номером.

        Забезпечує послідовність 1-10 згідно КМУ №205.
        """
        # Створюємо словник для швидкого доступу
        section_map = {s.get("id"): s for s in sections}

        ordered = []
        for section_id in sorted(KMU_205_STRUCTURE.keys(), key=int):
            if section_id in section_map:
                section = section_map[section_id]
                # Очищення внутрішніх полів
                clean_section = {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "content": section.get("content", ""),
                    "subsections": section.get("subsections", []),
                }
                ordered.append(clean_section)

        return ordered
