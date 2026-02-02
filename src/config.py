"""
Конфігурація додатку ENFORENCE.

Завантаження параметрів з .env файлу через Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Головні налаштування додатку."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./enforence.db"

    # LLM Providers
    mamay_llm_url: str = "https://enforence-run-8000.proxy.runpod.net"
    anthropic_api_key: str = ""
    default_llm_provider: str = "mamay"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "tz_samples"

    # Embedding
    embedding_model: str = "intfloat/multilingual-e5-large"

    # Generation
    max_generation_time: int = 300
    enable_parallel_generation: bool = True

    @property
    def is_development(self) -> bool:
        """Перевірка чи середовище є development."""
        return self.environment == "development"


settings = Settings()
