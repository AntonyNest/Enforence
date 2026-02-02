"""
Сервіс управління проєктами.

CRUD операції для проєктів ТЗ.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectModel
from src.models.project import ProjectCreate, ProjectUpdate
from src.utils.exceptions import ProjectNotFoundError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Сервіс для CRUD операцій з проєктами."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ProjectCreate) -> ProjectModel:
        """
        Створення нового проєкту.

        Args:
            data: Дані для створення проєкту.

        Returns:
            Створений проєкт.
        """
        project = ProjectModel(
            name=data.name,
            description=data.description,
            template_type=data.template_type,
            status="draft",
        )
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)

        logger.info("project_created", project_id=project.id, name=project.name)
        return project

    async def get_by_id(self, project_id: str) -> ProjectModel:
        """
        Отримання проєкту за ID.

        Args:
            project_id: Унікальний ідентифікатор проєкту.

        Returns:
            Знайдений проєкт.

        Raises:
            ProjectNotFoundError: Якщо проєкт не знайдено.
        """
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError(project_id)

        return project

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ProjectModel], int]:
        """
        Отримання списку проєктів з пагінацією.

        Args:
            skip: Зсув для пагінації.
            limit: Ліміт результатів.

        Returns:
            Кортеж (список проєктів, загальна кількість).
        """
        # Загальна кількість
        count_result = await self.session.execute(
            select(ProjectModel)
        )
        total = len(count_result.scalars().all())

        # Проєкти з пагінацією
        result = await self.session.execute(
            select(ProjectModel)
            .order_by(ProjectModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        projects = list(result.scalars().all())

        return projects, total

    async def update(
        self,
        project_id: str,
        data: ProjectUpdate,
    ) -> ProjectModel:
        """
        Оновлення проєкту.

        Args:
            project_id: ID проєкту.
            data: Дані для оновлення.

        Returns:
            Оновлений проєкт.
        """
        project = await self.get_by_id(project_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        await self.session.flush()
        await self.session.refresh(project)

        logger.info("project_updated", project_id=project_id)
        return project

    async def update_status(self, project_id: str, status: str) -> ProjectModel:
        """
        Оновлення статусу проєкту.

        Args:
            project_id: ID проєкту.
            status: Новий статус (draft, generating, completed, failed).

        Returns:
            Оновлений проєкт.
        """
        project = await self.get_by_id(project_id)
        project.status = status
        await self.session.flush()
        await self.session.refresh(project)

        logger.info("project_status_updated", project_id=project_id, status=status)
        return project
