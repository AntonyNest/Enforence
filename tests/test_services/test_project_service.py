"""
Тести для ProjectService.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import ProjectCreate, ProjectUpdate
from src.services.project_service import ProjectService
from src.utils.exceptions import ProjectNotFoundError


@pytest_asyncio.fixture
async def service(db_session: AsyncSession):
    """Сервіс проєктів з тестовою БД."""
    return ProjectService(db_session)


@pytest.mark.asyncio
async def test_create_and_get(service, sample_project_data):
    """Тест створення та отримання проєкту."""
    created = await service.create(ProjectCreate(**sample_project_data))
    fetched = await service.get_by_id(created.id)

    assert fetched.id == created.id
    assert fetched.name == sample_project_data["name"]


@pytest.mark.asyncio
async def test_update_project(service, sample_project_data):
    """Тест оновлення проєкту."""
    created = await service.create(ProjectCreate(**sample_project_data))
    updated = await service.update(
        created.id,
        ProjectUpdate(name="Оновлена назва"),
    )

    assert updated.name == "Оновлена назва"


@pytest.mark.asyncio
async def test_update_status(service, sample_project_data):
    """Тест оновлення статусу."""
    created = await service.create(ProjectCreate(**sample_project_data))
    updated = await service.update_status(created.id, "generating")

    assert updated.status == "generating"


@pytest.mark.asyncio
async def test_not_found_raises(service):
    """Тест помилки при пошуку неіснуючого проєкту."""
    with pytest.raises(ProjectNotFoundError):
        await service.get_by_id("fake-id")
