"""
Pydantic схеми для генерації ТЗ.
"""

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Запит на генерацію ТЗ."""

    requirements: dict[str, str] = Field(
        default_factory=dict,
        description="Додаткові вимоги для генерації",
    )
    sections: list[str] | None = Field(
        None,
        description="Конкретні секції для генерації (якщо не всі)",
    )


class GenerationStatusResponse(BaseModel):
    """Статус генерації ТЗ."""

    task_id: str
    status: str = Field(..., description="pending | processing | completed | failed")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Прогрес від 0 до 1")
    current_step: str | None = Field(None, description="Поточний крок генерації")
    elapsed_seconds: float | None = None
    error_message: str | None = None


class GenerationStartResponse(BaseModel):
    """Відповідь на початок генерації."""

    task_id: str
    status: str = "processing"
    estimated_time_seconds: int = 120


class ChatMessage(BaseModel):
    """Повідомлення чату для збору вимог."""

    role: str = Field(..., description="user | assistant")
    content: str = Field(..., description="Текст повідомлення")


class ChatRequest(BaseModel):
    """Запит чату для інтерактивного збору вимог."""

    message: str = Field(..., description="Повідомлення користувача")
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Відповідь чату."""

    message: str = Field(..., description="Відповідь асистента")
    requirements_complete: bool = Field(
        False, description="Чи зібрано достатньо вимог для генерації"
    )
    extracted_requirements: dict[str, str] = Field(default_factory=dict)
