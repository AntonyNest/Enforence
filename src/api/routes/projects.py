"""
CRUD endpoints для проєктів.
"""

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_project_service
from src.models.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from src.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Створення нового проєкту ТЗ.

    Args:
        data: Назва, опис, тип шаблону.

    Returns:
        Створений проєкт.
    """
    project = await service.create(data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    """
    Список проєктів з пагінацією.

    Args:
        skip: Зсув для пагінації.
        limit: Кількість результатів.

    Returns:
        Список проєктів та загальна кількість.
    """
    projects, total = await service.list_all(skip=skip, limit=limit)
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Отримання проєкту за ID.

    Args:
        project_id: Унікальний ідентифікатор.

    Returns:
        Знайдений проєкт.
    """
    project = await service.get_by_id(project_id)
    return ProjectResponse.model_validate(project)
