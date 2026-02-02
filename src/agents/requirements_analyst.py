"""
Агент аналізу вимог.

Збирає та структурує вимоги від користувача для генерації ТЗ.
"""

import json
from typing import Any

from src.agents.base import BaseAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

REQUIREMENTS_SYSTEM_PROMPT = """Ти — досвідчений аналітик вимог для технічних завдань в державній сфері України.

Твоя задача: проаналізувати опис проєкту та витягнути структуровані вимоги для генерації ТЗ згідно КМУ Постанова №205.

Для кожного проєкту визнач:
1. Тип системи (інформаційна, аналітична, портал послуг, тощо)
2. Цільова аудиторія
3. Основні функціональні вимоги
4. Нефункціональні вимоги (продуктивність, безпека, доступність)
5. Інтеграції з іншими системами
6. Вимоги до захисту інформації

Відповідай у форматі JSON."""

REQUIREMENTS_PROMPT_TEMPLATE = """Проаналізуй наступний проєкт та витягни структуровані вимоги:

Назва проєкту: {project_name}
Опис: {project_description}
{additional_requirements}

Поверни результат у форматі JSON з полями:
{{
    "system_type": "тип системи",
    "target_audience": "цільова аудиторія",
    "functional_requirements": ["список функціональних вимог"],
    "non_functional_requirements": ["список нефункціональних вимог"],
    "integrations": ["список інтеграцій"],
    "security_requirements": ["вимоги до безпеки"],
    "summary": "короткий підсумок вимог"
}}"""


class RequirementsAnalystAgent(BaseAgent):
    """
    Агент для аналізу та структурування вимог до ТЗ.

    Витягує з опису проєкту структуровані дані для
    подальшої генерації секцій ТЗ згідно КМУ №205.
    """

    name = "requirements_analyst"
    description = "Аналітик вимог для технічних завдань КМУ №205"
    role = "аналітик вимог"

    async def _process(self, **kwargs: Any) -> dict[str, Any]:
        """
        Аналіз вимог проєкту.

        Args:
            project_name: Назва проєкту.
            project_description: Опис проєкту.
            additional_requirements: Додаткові вимоги (опціонально).

        Returns:
            Структуровані вимоги у форматі dict.
        """
        project_name = kwargs.get("project_name", "")
        project_description = kwargs.get("project_description", "")
        additional = kwargs.get("additional_requirements", {})

        additional_text = ""
        if additional:
            additional_text = "\nДодаткові вимоги:\n"
            for key, value in additional.items():
                additional_text += f"- {key}: {value}\n"

        prompt = REQUIREMENTS_PROMPT_TEMPLATE.format(
            project_name=project_name,
            project_description=project_description,
            additional_requirements=additional_text,
        )

        response = await self.llm_router.route(
            task_type="requirements_analysis",
            prompt=prompt,
            system_prompt=REQUIREMENTS_SYSTEM_PROMPT,
            temperature=0.3,
        )

        # Парсинг JSON відповіді
        try:
            # Витягуємо JSON з відповіді
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            requirements = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            logger.warning(
                "requirements_parse_fallback",
                response_length=len(response.text),
            )
            requirements = {
                "summary": response.text,
                "raw_response": True,
            }

        logger.info(
            "requirements_analyzed",
            project=project_name,
            provider=response.provider,
        )

        return requirements
