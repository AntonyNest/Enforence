"""
Сервіс ембедінгів для семантичного пошуку.

Використовує multilingual-e5-large для підтримки української мови.
"""

import hashlib
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Сервіс для створення векторних представлень тексту.

    Використовує in-memory кешування для оптимізації.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Ліниве завантаження моделі ембедінгів."""
        if self._model is None:
            logger.info("loading_embedding_model", model=self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("embedding_model_loaded", model=self.model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        """
        Створення ембедінгу для тексту.

        Args:
            text: Вхідний текст українською або англійською.

        Returns:
            Вектор ембедінгу як список float.
        """
        cache_key = self._cache_key(text)
        return self._embed_cached(cache_key, text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Пакетне створення ембедінгів.

        Args:
            texts: Список текстів.

        Returns:
            Список векторів ембедінгів.
        """
        embeddings = self.model.encode(texts, show_progress_bar=False)
        logger.info("batch_embedding_complete", count=len(texts))
        return [emb.tolist() for emb in embeddings]

    @lru_cache(maxsize=1000)
    def _embed_cached(self, cache_key: str, text: str) -> list[float]:
        """
        Кешована генерація ембедінгу.

        Args:
            cache_key: Ключ кешу (MD5 хеш тексту).
            text: Вхідний текст.

        Returns:
            Вектор ембедінгу.
        """
        return self.model.encode(text, show_progress_bar=False).tolist()

    @staticmethod
    def _cache_key(text: str) -> str:
        """Генерація ключа кешу з тексту."""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    @property
    def embedding_dimension(self) -> int:
        """Розмірність вектора ембедінгів."""
        return self.model.get_sentence_embedding_dimension()
