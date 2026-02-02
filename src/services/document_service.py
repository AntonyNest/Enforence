"""
Сервіс управління документами ТЗ.

CRUD операції для згенерованих документів.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DocumentModel
from src.utils.exceptions import EnforenceException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Сервіс для роботи з документами ТЗ."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        project_id: str,
        sections: list[dict[str, Any]],
        compliance_score: float,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentModel:
        """
        Створення документу ТЗ.

        Args:
            project_id: ID проєкту.
            sections: Список секцій ТЗ.
            compliance_score: Оцінка відповідності.
            metadata: Додаткові метадані.

        Returns:
            Створений документ.
        """
        document = DocumentModel(
            project_id=project_id,
            sections=sections,
            compliance_score=compliance_score,
            metadata_json=metadata or {},
            status="completed",
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)

        logger.info(
            "document_created",
            document_id=document.id,
            project_id=project_id,
            compliance_score=compliance_score,
        )
        return document

    async def get_by_project_id(self, project_id: str) -> DocumentModel | None:
        """
        Отримання документу за ID проєкту.

        Args:
            project_id: ID проєкту.

        Returns:
            Документ або None якщо не знайдено.
        """
        result = await self.session.execute(
            select(DocumentModel)
            .where(DocumentModel.project_id == project_id)
            .order_by(DocumentModel.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def update_section(
        self,
        project_id: str,
        section_id: str,
        content: str,
    ) -> DocumentModel:
        """
        Оновлення окремої секції документу (Human-in-the-loop).

        Args:
            project_id: ID проєкту.
            section_id: Номер секції.
            content: Новий контент секції.

        Returns:
            Оновлений документ.

        Raises:
            EnforenceException: Якщо документ або секцію не знайдено.
        """
        document = await self.get_by_project_id(project_id)
        if not document:
            raise EnforenceException(f"Документ для проєкту {project_id} не знайдено")

        sections = document.sections or []
        updated = False

        for section in sections:
            if section.get("id") == section_id:
                section["content"] = content
                updated = True
                break

        if not updated:
            raise EnforenceException(f"Секцію {section_id} не знайдено в документі")

        document.sections = sections
        await self.session.flush()
        await self.session.refresh(document)

        logger.info(
            "section_updated",
            project_id=project_id,
            section_id=section_id,
        )
        return document
