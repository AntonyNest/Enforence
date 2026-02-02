"""
Семантичний пошук по базі знань ТЗ.

Використовує Qdrant для пошуку релевантних чанків.
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.config import settings
from src.rag.embeddings import EmbeddingService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGRetriever:
    """
    Семантичний пошук по індексованих документах ТЗ.

    Знаходить релевантні фрагменти з попередніх ТЗ
    для використання як контекст при генерації.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        qdrant_url: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_url = qdrant_url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.qdrant_client = QdrantClient(url=self.qdrant_url)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        section_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Семантичний пошук релевантних чанків.

        Args:
            query: Пошуковий запит (українською).
            top_k: Кількість результатів.
            section_filter: Фільтр по секції КМУ (напр. "2.1").

        Returns:
            Список результатів з текстом та метаданими.
        """
        # Генерація ембедінгу для запиту
        query_embedding = self.embedding_service.embed(query)

        # Побудова фільтра
        qdrant_filter = None
        if section_filter:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="section_id",
                        match=MatchValue(value=section_filter),
                    )
                ]
            )

        # Пошук у Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k,
        )

        # Форматування результатів
        search_results = []
        for point in results:
            search_results.append({
                "text": point.payload.get("text", ""),
                "score": point.score,
                "section_id": point.payload.get("section_id"),
                "section_title": point.payload.get("section_title"),
                "source_file": point.payload.get("source_file"),
            })

        logger.info(
            "rag_search_complete",
            query_length=len(query),
            results_count=len(search_results),
            top_score=search_results[0]["score"] if search_results else 0,
        )

        return search_results

    async def search_for_section(
        self,
        section_id: str,
        project_description: str,
        top_k: int = 3,
    ) -> str:
        """
        Пошук контексту для конкретної секції ТЗ.

        Args:
            section_id: Номер секції КМУ №205 (напр. "2").
            project_description: Опис проєкту для контексту.
            top_k: Кількість результатів.

        Returns:
            Об'єднаний текст релевантних чанків.
        """
        query = f"Секція {section_id} технічного завдання: {project_description}"

        results = await self.search(
            query=query,
            top_k=top_k,
            section_filter=section_id,
        )

        # Якщо фільтр по секції не дав результатів — шукаємо без фільтра
        if not results:
            results = await self.search(query=query, top_k=top_k)

        context_texts = [r["text"] for r in results]
        return "\n\n---\n\n".join(context_texts)

    async def health_check(self) -> bool:
        """Перевірка доступності Qdrant."""
        try:
            self.qdrant_client.get_collections()
            return True
        except Exception:
            return False
