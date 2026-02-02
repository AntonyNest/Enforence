"""
Агент перевірки відповідності КМУ №205.

Валідує згенерований ТЗ на відповідність структурі та вимогам.
"""

import json
from typing import Any

from src.agents.base import BaseAgent
from src.models.kmu_205 import KMU_205_STRUCTURE, get_mandatory_sections
from src.utils.logger import get_logger

logger = get_logger(__name__)

COMPLIANCE_SYSTEM_PROMPT = """Ти — експерт з нормативно-правової відповідності технічних завдань в Україні.

Твоя задача: перевірити технічне завдання на відповідність КМУ Постанова №205.

Оціни:
1. Наявність усіх обов'язкових секцій (1-8)
2. Повноту кожної секції (чи є всі підсекції)
3. Якість формулювань (офіційно-діловий стиль)
4. Конкретність вимог (не загальні фрази)
5. Відповідність термінології

Поверни оцінку у форматі JSON."""

COMPLIANCE_PROMPT_TEMPLATE = """Перевір наступне технічне завдання на відповідність КМУ Постанова №205.

Проєкт: {project_name}

Секції документу:
{sections_text}

Обов'язкові секції згідно КМУ №205 (1-8):
{mandatory_sections}

Поверни результат у форматі JSON:
{{
    "compliance_score": 0.0-1.0,
    "missing_sections": ["список відсутніх секцій"],
    "incomplete_sections": ["секції без підсекцій"],
    "warnings": ["попередження щодо якості"],
    "recommendations": ["рекомендації для покращення"],
    "section_scores": {{
        "1": 0.0-1.0,
        "2": 0.0-1.0
    }}
}}"""


class ComplianceCheckerAgent(BaseAgent):
    """
    Агент для перевірки відповідності ТЗ вимогам КМУ №205.

    Використовує Claude для глибокого аналізу
    (reasoning capabilities кращі за MamayLM).
    """

    name = "compliance_checker"
    description = "Перевірка відповідності ТЗ нормам КМУ №205"
    role = "експерт з нормативної відповідності"

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Перевірка відповідності документу КМУ №205.

        Args:
            project_name: Назва проєкту.
            sections: Список згенерованих секцій.

        Returns:
            Результат перевірки з оцінкою та рекомендаціями.
        """
        project_name = kwargs.get("project_name", "")
        sections = kwargs.get("sections", [])

        # Структурна перевірка (без LLM)
        structural_result = self._structural_check(sections)

        # Семантична перевірка через Claude
        sections_text = self._format_sections(sections)
        mandatory_text = self._format_mandatory_sections()

        prompt = COMPLIANCE_PROMPT_TEMPLATE.format(
            project_name=project_name,
            sections_text=sections_text,
            mandatory_sections=mandatory_text,
        )

        response = await self.llm_router.route(
            task_type="compliance_check",
            prompt=prompt,
            system_prompt=COMPLIANCE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2048,
        )

        # Парсинг відповіді Claude
        try:
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            llm_result = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            logger.warning("compliance_parse_fallback")
            llm_result = {}

        # Об'єднання структурної та семантичної перевірки
        result = {
            "compliance_score": llm_result.get(
                "compliance_score", structural_result["structural_score"]
            ),
            "structural_score": structural_result["structural_score"],
            "missing_sections": structural_result["missing_sections"],
            "incomplete_sections": llm_result.get("incomplete_sections", []),
            "warnings": llm_result.get("warnings", []),
            "recommendations": llm_result.get("recommendations", []),
            "section_scores": llm_result.get("section_scores", {}),
            "provider": response.provider,
        }

        logger.info(
            "compliance_check_complete",
            score=result["compliance_score"],
            missing=len(result["missing_sections"]),
        )

        return result

    @staticmethod
    def _structural_check(sections: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Структурна перевірка наявності обов'язкових секцій.

        Не потребує LLM — просто перевіряє наявність.
        """
        mandatory = get_mandatory_sections()
        present_ids = {s.get("id") for s in sections}
        missing = [sid for sid in mandatory if sid not in present_ids]

        score = (len(mandatory) - len(missing)) / len(mandatory) if mandatory else 1.0

        return {
            "structural_score": round(score, 2),
            "missing_sections": missing,
            "present_sections": list(present_ids),
        }

    @staticmethod
    def _format_sections(sections: list[dict[str, Any]]) -> str:
        """Форматування секцій для промпту."""
        parts = []
        for section in sections:
            sid = section.get("id", "?")
            title = section.get("title", "")
            content = section.get("content", "")
            preview = content[:500] + "..." if len(content) > 500 else content
            parts.append(f"\n--- Секція {sid}: {title} ---\n{preview}")
        return "\n".join(parts)

    @staticmethod
    def _format_mandatory_sections() -> str:
        """Форматування списку обов'язкових секцій."""
        lines = []
        for sid in get_mandatory_sections():
            info = KMU_205_STRUCTURE.get(sid, {})
            lines.append(f"{sid}. {info.get('title', '')}")
        return "\n".join(lines)
