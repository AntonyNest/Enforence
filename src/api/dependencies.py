"""
Dependency Injection для FastAPI.

Фабрики сервісів та залежностей.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db_session
from src.services.document_service import DocumentService
from src.services.export_service import ExportService
from src.services.generation_service import GenerationService
from src.services.project_service import ProjectService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Отримання сесії бази даних."""
    async for session in get_db_session():
        yield session


async def get_project_service(
    session: AsyncSession = Depends(get_session),
) -> ProjectService:
    """Отримання сервісу проєктів."""
    return ProjectService(session)


async def get_document_service(
    session: AsyncSession = Depends(get_session),
) -> DocumentService:
    """Отримання сервісу документів."""
    return DocumentService(session)


async def get_generation_service(
    session: AsyncSession = Depends(get_session),
) -> GenerationService:
    """Отримання сервісу генерації."""
    return GenerationService(session)


async def get_export_service(
    session: AsyncSession = Depends(get_session),
) -> ExportService:
    """Отримання сервісу експорту."""
    return ExportService(session)
