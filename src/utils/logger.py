"""
Структуроване логування для ENFORENCE.

Використовує structlog для JSON-формату логів.
"""

import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Налаштування структурованого логування.

    Args:
        log_level: Рівень логування (DEBUG, INFO, WARNING, ERROR).
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Отримання логера з контекстом.

    Args:
        name: Ім'я модуля для контексту логера.

    Returns:
        Налаштований структурований логер.
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(module=name)
    return logger
