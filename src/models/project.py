"""
Pydantic схеми для проєктів.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Схема для створення проєкту."""

    name: str = Field(..., min_length=3, max_length=255, description="Назва проєкту")
    description: str | None = Field(None, description="Опис проєкту")
    template_type: str = Field("kmu_205", description="Тип шаблону ТЗ")


class ProjectUpdate(BaseModel):
    """Схема для оновлення проєкту."""

    name: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    """Схема відповіді проєкту."""

    id: str
    name: str
    description: str | None = None
    template_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Схема для списку проєктів."""

    items: list[ProjectResponse]
    total: int
