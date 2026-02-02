"""
Точка входу ENFORENCE API.

Ініціалізація FastAPI, налаштування логування, запуск сервера.
"""

import uvicorn

from src.api.app import create_app
from src.config import settings
from src.utils.logger import setup_logging

# Налаштування логування
log_level = "DEBUG" if settings.is_development else "INFO"
setup_logging(log_level)

# Створення FastAPI додатку
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
    )
