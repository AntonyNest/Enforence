"""
Сервіс оркестрації генерації ТЗ.

Координує роботу всіх агентів для генерації повного документу.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.compliance_checker import ComplianceCheckerAgent
from src.agents.document_assembler import DocumentAssemblerAgent
from src.agents.rag_retriever import RAGRetrieverAgent
from src.agents.requirements_analyst import RequirementsAnalystAgent
from src.agents.section_generator import SectionGeneratorAgent
from src.config import settings
from src.db.models import GenerationTaskModel
from src.services.document_service import DocumentService
from src.services.project_service import ProjectService
from src.utils.exceptions import GenerationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GenerationService:
    """
    Оркестратор генерації ТЗ.

    Координує послідовність дій:
    1. Аналіз вимог (RequirementsAnalyst)
    2. RAG пошук контексту (RAGRetriever)
    3. Паралельна генерація секцій (SectionGenerator)
    4. Перевірка відповідності (ComplianceChecker)
    5. Збірка документу (DocumentAssembler)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_service = ProjectService(session)
        self.document_service = DocumentService(session)

        # Ініціалізація агентів
        self.requirements_analyst = RequirementsAnalystAgent()
        self.rag_retriever = RAGRetrieverAgent()
        self.section_generator = SectionGeneratorAgent()
        self.compliance_checker = ComplianceCheckerAgent()
        self.document_assembler = DocumentAssemblerAgent()

    async def start_generation(
        self,
        project_id: str,
        additional_requirements: dict[str, str] | None = None,
    ) -> GenerationTaskModel:
        """
        Початок генерації ТЗ.

        Створює task і запускає генерацію у фоні.

        Args:
            project_id: ID проєкту.
            additional_requirements: Додаткові вимоги.

        Returns:
            Модель завдання генерації.
        """
        project = await self.project_service.get_by_id(project_id)

        # Створення завдання генерації
        task = GenerationTaskModel(
            project_id=project_id,
            status="processing",
            progress=0.0,
            current_step="Ініціалізація генерації",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)

        # Оновлення статусу проєкту
        await self.project_service.update_status(project_id, "generating")

        # Запуск генерації у фоновій задачі
        asyncio.create_task(
            self._run_generation(
                task_id=task.id,
                project_id=project.id,
                project_name=project.name,
                project_description=project.description or "",
                additional_requirements=additional_requirements or {},
            )
        )

        logger.info(
            "generation_started",
            task_id=task.id,
            project_id=project_id,
        )

        return task

    async def _run_generation(
        self,
        task_id: str,
        project_id: str,
        project_name: str,
        project_description: str,
        additional_requirements: dict[str, str],
    ) -> None:
        """
        Повний пайплайн генерації ТЗ.

        Args:
            task_id: ID завдання генерації.
            project_id: ID проєкту.
            project_name: Назва проєкту.
            project_description: Опис проєкту.
            additional_requirements: Додаткові вимоги.
        """
        try:
            # Крок 1: Аналіз вимог (10%)
            await self._update_task(task_id, 0.1, "Аналіз вимог проєкту")
            requirements = await self.requirements_analyst.execute(
                project_name=project_name,
                project_description=project_description,
                additional_requirements=additional_requirements,
            )

            # Крок 2: RAG пошук контексту (20%)
            await self._update_task(task_id, 0.2, "Пошук релевантного контексту")
            rag_result = await self.rag_retriever.execute(
                project_description=project_description,
                requirements=requirements,
            )
            contexts = rag_result.get("contexts", {})

            # Крок 3: Генерація секцій (20-80%)
            if settings.enable_parallel_generation:
                sections = await self._generate_sections_parallel(
                    task_id=task_id,
                    project_name=project_name,
                    project_description=project_description,
                    requirements=requirements,
                    contexts=contexts,
                )
            else:
                sections = await self._generate_sections_sequential(
                    task_id=task_id,
                    project_name=project_name,
                    project_description=project_description,
                    requirements=requirements,
                    contexts=contexts,
                )

            # Крок 4: Перевірка відповідності (90%)
            await self._update_task(task_id, 0.9, "Перевірка відповідності КМУ №205")
            compliance_result = await self.compliance_checker.execute(
                project_name=project_name,
                sections=sections,
            )

            # Крок 5: Збірка документу (95%)
            await self._update_task(task_id, 0.95, "Збірка фінального документу")
            document = await self.document_assembler.execute(
                project_id=project_id,
                project_name=project_name,
                sections=sections,
                compliance_result=compliance_result,
                requirements=requirements,
            )

            # Збереження документу в БД
            await self.document_service.create(
                project_id=project_id,
                sections=document.get("sections", []),
                compliance_score=document.get("compliance_score", 0.0),
                metadata=document.get("metadata", {}),
            )

            # Завершення
            await self._update_task(task_id, 1.0, "Генерація завершена", status="completed")
            await self.project_service.update_status(project_id, "completed")

            logger.info(
                "generation_complete",
                task_id=task_id,
                project_id=project_id,
                compliance_score=document.get("compliance_score"),
            )

        except Exception as e:
            logger.error(
                "generation_failed",
                task_id=task_id,
                project_id=project_id,
                error=str(e),
            )
            await self._update_task(
                task_id, 0.0, f"Помилка: {str(e)}", status="failed", error=str(e)
            )
            await self.project_service.update_status(project_id, "failed")

    async def _generate_sections_parallel(
        self,
        task_id: str,
        project_name: str,
        project_description: str,
        requirements: dict[str, Any],
        contexts: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Паралельна генерація всіх секцій."""
        await self._update_task(task_id, 0.3, "Паралельна генерація секцій")

        tasks = []
        for section_id in [str(i) for i in range(1, 11)]:
            task = self.section_generator.execute(
                section_id=section_id,
                project_name=project_name,
                project_description=project_description,
                requirements=requirements,
                rag_context=contexts.get(section_id, ""),
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sections = []
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                logger.error(f"section_{i}_generation_failed", error=str(result))
                sections.append({
                    "id": str(i),
                    "title": f"Секція {i}",
                    "content": f"[Помилка генерації: {result}]",
                    "subsections": [],
                })
            else:
                sections.append(result)

        return sections

    async def _generate_sections_sequential(
        self,
        task_id: str,
        project_name: str,
        project_description: str,
        requirements: dict[str, Any],
        contexts: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Послідовна генерація секцій з прогресом."""
        sections = []

        for i in range(1, 11):
            section_id = str(i)
            progress = 0.2 + (0.6 * i / 10)
            await self._update_task(
                task_id, progress, f"Генерація секції {section_id}"
            )

            result = await self.section_generator.execute(
                section_id=section_id,
                project_name=project_name,
                project_description=project_description,
                requirements=requirements,
                rag_context=contexts.get(section_id, ""),
            )
            sections.append(result)

        return sections

    async def _update_task(
        self,
        task_id: str,
        progress: float,
        step: str,
        status: str = "processing",
        error: str | None = None,
    ) -> None:
        """Оновлення прогресу задачі генерації."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(GenerationTaskModel).where(GenerationTaskModel.id == task_id)
        )
        task = result.scalar_one_or_none()

        if task:
            task.progress = progress
            task.current_step = step
            task.status = status
            if error:
                task.error_message = error
            if status in ("completed", "failed"):
                task.completed_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def get_task_status(self, task_id: str) -> GenerationTaskModel | None:
        """Отримання статусу завдання генерації."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(GenerationTaskModel).where(GenerationTaskModel.id == task_id)
        )
        return result.scalar_one_or_none()
