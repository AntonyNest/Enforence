"""
Endpoints для документів ТЗ та експорту.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse

from src.api.dependencies import get_document_service, get_export_service
from src.models.document import DocumentResponse, SectionUpdate
from src.models.kmu_205 import KMU_205_STRUCTURE
from src.services.document_service import DocumentService
from src.services.export_service import ExportService

router = APIRouter()


@router.get("/{project_id}/document", response_model=DocumentResponse)
async def get_document(
    project_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse | JSONResponse:
    """
    Отримання згенерованого ТЗ у JSON форматі.

    Args:
        project_id: ID проєкту.

    Returns:
        Повний документ ТЗ з секціями та метаданими.
    """
    document = await service.get_by_project_id(project_id)

    if not document:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Документ для проєкту {project_id} не знайдено"},
        )

    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        sections=document.sections or [],
        compliance_score=document.compliance_score,
        metadata=document.metadata_json or {},
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.patch("/{project_id}/sections/{section_id}")
async def update_section(
    project_id: str,
    section_id: str,
    data: SectionUpdate,
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """
    Оновлення окремої секції ТЗ (Human-in-the-loop).

    Дозволяє редагувати згенерований контент.

    Args:
        project_id: ID проєкту.
        section_id: Номер секції (1-10).
        data: Новий контент секції.

    Returns:
        Підтвердження оновлення.
    """
    await service.update_section(
        project_id=project_id,
        section_id=section_id,
        content=data.content,
    )

    return {"status": "updated", "section_id": section_id}


@router.get("/{project_id}/export/docx")
async def export_docx(
    project_id: str,
    service: ExportService = Depends(get_export_service),
) -> FileResponse:
    """
    Експорт ТЗ у DOCX формат.

    Args:
        project_id: ID проєкту.

    Returns:
        DOCX файл для завантаження.
    """
    file_path = await service.export_docx(project_id)

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"tz_{project_id[:8]}.docx",
    )


@router.get("/templates", tags=["Templates"])
async def list_templates() -> dict:
    """
    Список доступних шаблонів ТЗ.

    Returns:
        Шаблони КМУ №205 зі структурою секцій.
    """
    return {
        "templates": [
            {
                "id": "kmu_205",
                "name": "КМУ Постанова №205",
                "description": "Технічне завдання на створення засобу інформатизації",
                "sections": [
                    {
                        "id": section_id,
                        "title": section["title"],
                        "mandatory": section["mandatory"],
                        "subsections_count": len(section.get("subsections", [])),
                    }
                    for section_id, section in KMU_205_STRUCTURE.items()
                ],
            }
        ]
    }
