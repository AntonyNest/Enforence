"""
Користувацькі виключення для ENFORENCE.
"""


class EnforenceException(Exception):
    """Базове виключення ENFORENCE."""

    def __init__(self, message: str = "Внутрішня помилка сервісу") -> None:
        self.message = message
        super().__init__(self.message)


class LLMError(EnforenceException):
    """Помилка LLM API (MamayLM або Claude)."""

    def __init__(self, message: str = "Помилка LLM провайдера", provider: str = "unknown") -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class RAGError(EnforenceException):
    """Помилка RAG пайплайну (embedding, retrieval, Qdrant)."""

    def __init__(self, message: str = "Помилка RAG пайплайну") -> None:
        super().__init__(message)


class GenerationError(EnforenceException):
    """Помилка генерації ТЗ."""

    def __init__(self, message: str = "Помилка генерації документу") -> None:
        super().__init__(message)


class ComplianceError(EnforenceException):
    """Помилка валідації відповідності КМУ №205."""

    def __init__(self, message: str = "Документ не відповідає КМУ №205") -> None:
        super().__init__(message)


class ProjectNotFoundError(EnforenceException):
    """Проєкт не знайдено."""

    def __init__(self, project_id: str) -> None:
        super().__init__(f"Проєкт з ID {project_id} не знайдено")
        self.project_id = project_id


class ExportError(EnforenceException):
    """Помилка експорту документу."""

    def __init__(self, message: str = "Помилка експорту документу") -> None:
        super().__init__(message)
