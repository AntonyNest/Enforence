"""
Pydantic схеми для документів ТЗ.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SubsectionContent(BaseModel):
    """Контент підсекції ТЗ."""

    id: str = Field(..., description="Номер підсекції (напр. '1.1')")
    title: str = Field(..., description="Назва підсекції")
    content: str = Field("", description="Текст підсекції")


class SectionContent(BaseModel):
    """Контент секції ТЗ."""

    id: str = Field(..., description="Номер секції (напр. '1')")
    title: str = Field(..., description="Назва секції")
    content: str = Field("", description="Загальний текст секції")
    subsections: list[SubsectionContent] = Field(default_factory=list)


class SectionUpdate(BaseModel):
    """Схема для оновлення секції (Human-in-the-loop)."""

    content: str = Field(..., description="Оновлений текст секції")


class DocumentResponse(BaseModel):
    """Повна відповідь документу ТЗ."""

    id: str
    project_id: str
    sections: list[SectionContent] = Field(default_factory=list)
    compliance_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
