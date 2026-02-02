"""
SQLAlchemy ORM моделі для ENFORENCE.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


def generate_uuid() -> str:
    """Генерація UUID."""
    return str(uuid.uuid4())


class ProjectModel(Base):
    """Модель проєкту ТЗ."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(50), default="kmu_205", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DocumentModel(Base):
    """Модель згенерованого ТЗ документу."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sections: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class GenerationTaskModel(Base):
    """Модель завдання генерації ТЗ."""

    __tablename__ = "generation_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
