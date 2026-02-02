"""
Агент генерації секцій ТЗ.

Генерує контент для кожної секції згідно КМУ №205
з використанням RAG контексту.
"""

from typing import Any

from src.agents.base import BaseAgent
from src.models.kmu_205 import KMU_205_STRUCTURE, get_all_subsections
from src.utils.logger import get_logger

logger = get_logger(__name__)

SECTION_SYSTEM_PROMPT = """Ти — експерт зі складання технічних завдань згідно КМУ Постанова №205.

Правила:
1. Писати виключно українською мовою (офіційно-діловий стиль)
2. Використовувати термінологію з нормативних документів України
3. Конкретизувати вимоги (не загальні фрази, а конкретні параметри)
4. Структурувати текст з нумерованими пунктами
5. Враховувати контекст з попередніх ТЗ (RAG)"""

SECTION_PROMPT_TEMPLATE = """Згенеруй секцію "{section_id}. {section_title}" технічного завдання.

Проєкт: {project_name}
Опис: {project_description}

Вимоги:
{requirements_text}

Контекст з попередніх ТЗ:
{rag_context}

{subsections_instruction}

Важливо:
- Текст повинен бути конкретним та специфічним для даного проєкту
- Використовуй офіційно-діловий стиль
- Кожен пункт має бути чітко сформульований
- Обсяг: 300-800 слів для секції"""


class SectionGeneratorAgent(BaseAgent):
    """
    Агент для генерації контенту окремих секцій ТЗ.

    Генерує текст кожної секції КМУ №205 з урахуванням:
    - Опису проєкту та вимог
    - RAG контексту з попередніх ТЗ
    - Структури підсекцій
    """

    name = "section_generator"
    description = "Генерація секцій ТЗ згідно КМУ №205"
    role = "технічний письменник ТЗ"

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Генерація однієї секції ТЗ.

        Args:
            section_id: Номер секції (1-10).
            project_name: Назва проєкту.
            project_description: Опис проєкту.
            requirements: Структуровані вимоги.
            rag_context: Контекст з RAG пошуку.

        Returns:
            Словник з id, title, content, subsections.
        """
        section_id = kwargs.get("section_id", "1")
        project_name = kwargs.get("project_name", "")
        project_description = kwargs.get("project_description", "")
        requirements = kwargs.get("requirements", {})
        rag_context = kwargs.get("rag_context", "")

        section_info = KMU_205_STRUCTURE.get(section_id, {})
        section_title = section_info.get("title", f"Секція {section_id}")

        # Підготовка тексту вимог
        requirements_text = self._format_requirements(requirements)

        # Підготовка інструкцій для підсекцій
        subsections = get_all_subsections(section_id)
        subsections_instruction = self._format_subsections_instruction(subsections)

        prompt = SECTION_PROMPT_TEMPLATE.format(
            section_id=section_id,
            section_title=section_title,
            project_name=project_name,
            project_description=project_description,
            requirements_text=requirements_text,
            rag_context=rag_context or "Контекст не знайдено.",
            subsections_instruction=subsections_instruction,
        )

        response = await self.llm_router.route(
            task_type="section_generation",
            prompt=prompt,
            system_prompt=SECTION_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=4096,
        )

        result = {
            "id": section_id,
            "title": section_title,
            "content": response.text,
            "subsections": [
                {"id": sub["id"], "title": sub["title"], "content": ""}
                for sub in subsections
            ],
            "provider": response.provider,
            "tokens_used": response.tokens_used,
        }

        logger.info(
            "section_generated",
            section_id=section_id,
            tokens=response.tokens_used,
            duration_ms=round(response.duration_ms, 2),
            provider=response.provider,
        )

        return result

    async def generate_all_sections(
        self,
        project_name: str,
        project_description: str,
        requirements: dict[str, Any],
        contexts: dict[str, str],
    ) -> list[dict[str, Any]]:
        """
        Генерація всіх 10 секцій ТЗ.

        Args:
            project_name: Назва проєкту.
            project_description: Опис проєкту.
            requirements: Структуровані вимоги.
            contexts: RAG контексти по секціях.

        Returns:
            Список згенерованих секцій.
        """
        sections = []

        for section_id in sorted(KMU_205_STRUCTURE.keys(), key=int):
            result = await self.execute(
                section_id=section_id,
                project_name=project_name,
                project_description=project_description,
                requirements=requirements,
                rag_context=contexts.get(section_id, ""),
            )
            sections.append(result)

        return sections

    @staticmethod
    def _format_requirements(requirements: dict[str, Any]) -> str:
        """Форматування вимог для промпту."""
        parts = []

        if summary := requirements.get("summary"):
            parts.append(f"Загальний опис: {summary}")

        if func_reqs := requirements.get("functional_requirements"):
            parts.append("Функціональні вимоги:")
            for req in func_reqs:
                parts.append(f"  - {req}")

        if nfr := requirements.get("non_functional_requirements"):
            parts.append("Нефункціональні вимоги:")
            for req in nfr:
                parts.append(f"  - {req}")

        if security := requirements.get("security_requirements"):
            parts.append("Вимоги до безпеки:")
            for req in security:
                parts.append(f"  - {req}")

        return "\n".join(parts) if parts else "Вимоги не уточнено."

    @staticmethod
    def _format_subsections_instruction(subsections: list[dict[str, str]]) -> str:
        """Формування інструкцій для підсекцій."""
        if not subsections:
            return ""

        lines = ["Секція повинна містити наступні підсекції:"]
        for sub in subsections:
            lines.append(f"  {sub['id']}. {sub['title']}: {sub.get('description', '')}")

        return "\n".join(lines)
