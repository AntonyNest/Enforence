"""
Фікстури для тестів ENFORENCE.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.models import DocumentModel, GenerationTaskModel, ProjectModel  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_enforence.db"


@pytest_asyncio.fixture
async def db_engine():
    """Створення тестового двигуна БД."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Створення тестової сесії БД."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_project_data():
    """Тестові дані для проєкту."""
    return {
        "name": "Тестовий портал е-послуг",
        "description": "Веб-портал для надання електронних послуг громадянам",
        "template_type": "kmu_205",
    }


@pytest.fixture
def sample_requirements():
    """Тестові вимоги до проєкту."""
    return {
        "system_type": "Веб-портал",
        "target_audience": "Громадяни України",
        "functional_requirements": [
            "Реєстрація та авторизація користувачів",
            "Подача електронних заяв",
            "Відстеження статусу заяви",
        ],
        "non_functional_requirements": [
            "Час відповіді < 3 секунди",
            "Доступність 99.9%",
        ],
        "security_requirements": [
            "Шифрування персональних даних",
            "Двофакторна автентифікація",
        ],
        "summary": "Портал е-послуг для громадян",
    }
