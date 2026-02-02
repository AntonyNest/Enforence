"""
Тести для CRUD endpoints проєктів.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import ProjectCreate
from src.services.project_service import ProjectService


@pytest_asyncio.fixture
async def project_service(db_session: AsyncSession):
    """Сервіс проєктів з тестовою БД."""
    return ProjectService(db_session)


@pytest.mark.asyncio
async def test_create_project(project_service, sample_project_data):
    """Тест створення проєкту."""
    data = ProjectCreate(**sample_project_data)
    project = await project_service.create(data)

    assert project.id is not None
    assert project.name == sample_project_data["name"]
    assert project.status == "draft"
    assert project.template_type == "kmu_205"


@pytest.mark.asyncio
async def test_get_project(project_service, sample_project_data):
    """Тест отримання проєкту за ID."""
    data = ProjectCreate(**sample_project_data)
    created = await project_service.create(data)

    project = await project_service.get_by_id(created.id)
    assert project.name == sample_project_data["name"]


@pytest.mark.asyncio
async def test_list_projects(project_service, sample_project_data):
    """Тест списку проєктів."""
    data = ProjectCreate(**sample_project_data)
    await project_service.create(data)
    await project_service.create(data)

    projects, total = await project_service.list_all()
    assert total >= 2
    assert len(projects) >= 2


@pytest.mark.asyncio
async def test_project_not_found(project_service):
    """Тест помилки при пошуку неіснуючого проєкту."""
    from src.utils.exceptions import ProjectNotFoundError

    with pytest.raises(ProjectNotFoundError):
        await project_service.get_by_id("nonexistent-id")
