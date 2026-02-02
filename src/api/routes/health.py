"""
Health check endpoint.
"""

from fastapi import APIRouter

from src.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Перевірка стану сервісу.

    Returns:
        Статус сервісу та версія.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }
