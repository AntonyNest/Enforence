"""
Endpoints для генерації ТЗ.
"""

import time

from fastapi import APIRouter, Depends

from src.api.dependencies import get_generation_service
from src.models.generation import (
    GenerationRequest,
    GenerationStartResponse,
    GenerationStatusResponse,
)
from src.services.generation_service import GenerationService

router = APIRouter()


@router.post("/{project_id}/generate", response_model=GenerationStartResponse, status_code=202)
async def start_generation(
    project_id: str,
    data: GenerationRequest | None = None,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationStartResponse:
    """
    Запуск генерації ТЗ для проєкту.

    Повертає task_id для відстеження прогресу.

    Args:
        project_id: ID проєкту.
        data: Додаткові вимоги (опціонально).

    Returns:
        ID завдання та статус.
    """
    requirements = data.requirements if data else {}

    task = await service.start_generation(
        project_id=project_id,
        additional_requirements=requirements,
    )

    return GenerationStartResponse(
        task_id=task.id,
        status="processing",
        estimated_time_seconds=120,
    )


@router.get("/{project_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    project_id: str,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationStatusResponse:
    """
    Отримання статусу генерації ТЗ.

    Використовується для polling з фронтенду.

    Args:
        project_id: ID проєкту.

    Returns:
        Поточний статус, прогрес, крок генерації.
    """
    from sqlalchemy import select

    from src.db.models import GenerationTaskModel

    # Знаходимо останній task для проєкту
    result = await service.session.execute(
        select(GenerationTaskModel)
        .where(GenerationTaskModel.project_id == project_id)
        .order_by(GenerationTaskModel.created_at.desc())
    )
    task = result.scalar_one_or_none()

    if not task:
        return GenerationStatusResponse(
            task_id="",
            status="not_found",
            progress=0.0,
            current_step="Генерацію не розпочато",
        )

    elapsed = None
    if task.started_at:
        elapsed = time.time() - task.started_at.timestamp()

    return GenerationStatusResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        elapsed_seconds=round(elapsed, 1) if elapsed else None,
        error_message=task.error_message,
    )
