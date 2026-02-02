"""
Ініціалізація бази даних SQLite.

Створення всіх таблиць згідно SQLAlchemy моделей.
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings
from src.db.base import Base
from src.db.models import DocumentModel, GenerationTaskModel, ProjectModel  # noqa: F401


async def init_db() -> None:
    """Створення всіх таблиць у базі даних."""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("База даних ініціалізована успішно!")
    print(f"URL: {settings.database_url}")


if __name__ == "__main__":
    asyncio.run(init_db())
