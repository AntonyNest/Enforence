"""
FastAPI додаток ENFORENCE.

Конфігурація CORS, middleware, обробка помилок.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import documents, generation, health, projects
from src.config import settings
from src.utils.exceptions import EnforenceException, ProjectNotFoundError


def create_app() -> FastAPI:
    """
    Створення та налаштування FastAPI додатку.

    Returns:
        Налаштований FastAPI додаток.
    """
    app = FastAPI(
        title="ENFORENCE API",
        description=(
            "AI-платформа для автоматизованої генерації "
            "технічних завдань (ТЗ) згідно КМУ Постанова №205"
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS для фронтенду Марії
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Реєстрація роутерів
    app.include_router(health.router, tags=["Health"])
    app.include_router(
        projects.router,
        prefix="/api/v1/projects",
        tags=["Projects"],
    )
    app.include_router(
        generation.router,
        prefix="/api/v1/projects",
        tags=["Generation"],
    )
    app.include_router(
        documents.router,
        prefix="/api/v1/projects",
        tags=["Documents"],
    )

    # Обробка помилок
    _register_error_handlers(app)

    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Реєстрація глобальних обробників помилок."""

    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found_handler(
        request: Request, exc: ProjectNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message},
        )

    @app.exception_handler(EnforenceException)
    async def enforence_error_handler(
        request: Request, exc: EnforenceException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message},
        )
