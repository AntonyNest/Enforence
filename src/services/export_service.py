"""
Сервіс експорту документів ТЗ.

Конвертація JSON документу у DOCX формат.
"""

from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.document_service import DocumentService
from src.utils.docx_export import create_tz_document, save_document
from src.utils.exceptions import ExportError
from src.utils.logger import get_logger

logger = get_logger(__name__)

EXPORTS_DIR = Path("data/exports")


class ExportService:
    """Сервіс для експорту ТЗ у різні формати."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.document_service = DocumentService(session)

    async def export_docx(self, project_id: str) -> Path:
        """
        Експорт ТЗ у DOCX формат.

        Args:
            project_id: ID проєкту.

        Returns:
            Шлях до згенерованого DOCX файлу.

        Raises:
            ExportError: Якщо документ не знайдено або помилка експорту.
        """
        document = await self.document_service.get_by_project_id(project_id)

        if not document:
            raise ExportError(f"Документ для проєкту {project_id} не знайдено")

        sections = document.sections or []
        metadata: dict[str, Any] = document.metadata_json or {}
        metadata["project_id"] = project_id

        try:
            doc = create_tz_document(sections, metadata)

            # Назва файлу на основі проєкту
            safe_name = project_id[:8]
            output_path = EXPORTS_DIR / f"tz_{safe_name}.docx"

            saved_path = save_document(doc, output_path)

            logger.info(
                "docx_exported",
                project_id=project_id,
                path=str(saved_path),
            )

            return saved_path

        except Exception as e:
            raise ExportError(f"Помилка експорту DOCX: {e}") from e
