"""
Пайплайн інгестії документів: DOCX → чанки → Qdrant.

Обробляє зразки ТЗ для побудови бази знань RAG.
"""

from pathlib import Path
from typing import Any

from docx import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config import settings
from src.rag.chunker import DocumentChunker
from src.rag.embeddings import EmbeddingService
from src.utils.exceptions import RAGError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentIngestionPipeline:
    """
    Пайплайн для інгестії DOCX документів у Qdrant.

    Етапи:
    1. Читання DOCX файлу
    2. Розбиття на чанки з урахуванням структури КМУ №205
    3. Генерація ембедінгів
    4. Завантаження у Qdrant
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        chunker: DocumentChunker | None = None,
        qdrant_url: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.chunker = chunker or DocumentChunker()
        self.qdrant_url = qdrant_url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.qdrant_client = QdrantClient(url=self.qdrant_url)

    def ensure_collection(self) -> None:
        """
        Створення колекції у Qdrant якщо не існує.

        Налаштовує векторні параметри під multilingual-e5-large.
        """
        collections = self.qdrant_client.get_collections().collections
        existing_names = [c.name for c in collections]

        if self.collection_name not in existing_names:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_service.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                "qdrant_collection_created",
                collection=self.collection_name,
                dimension=self.embedding_service.embedding_dimension,
            )

    def read_docx(self, file_path: Path) -> str:
        """
        Читання тексту з DOCX файлу.

        Args:
            file_path: Шлях до DOCX файлу.

        Returns:
            Повний текст документу.

        Raises:
            RAGError: Якщо файл не знайдено або пошкоджено.
        """
        try:
            doc = Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            logger.info(
                "docx_read",
                file=file_path.name,
                paragraphs=len(paragraphs),
                chars=len(text),
            )
            return text
        except Exception as e:
            raise RAGError(f"Помилка читання DOCX {file_path}: {e}") from e

    def ingest_file(self, file_path: Path) -> int:
        """
        Інгестія одного DOCX файлу в Qdrant.

        Args:
            file_path: Шлях до DOCX файлу.

        Returns:
            Кількість створених чанків.
        """
        self.ensure_collection()

        # 1. Читання DOCX
        text = self.read_docx(file_path)

        # 2. Розбиття на чанки
        chunks = self.chunker.chunk_document(text, source_file=file_path.name)

        if not chunks:
            logger.warning("no_chunks_produced", file=file_path.name)
            return 0

        # 3. Генерація ембедінгів
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(texts)

        # 4. Завантаження у Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            payload: dict[str, Any] = {
                "text": chunk.text,
                "source_file": chunk.source_file,
                "section_id": chunk.section_id,
                "section_title": chunk.section_title,
                "chunk_index": chunk.chunk_index,
            }
            points.append(
                PointStruct(
                    id=i + self._get_collection_count(),
                    vector=embedding,
                    payload=payload,
                )
            )

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info(
            "file_ingested",
            file=file_path.name,
            chunks=len(points),
        )

        return len(points)

    def ingest_directory(self, directory: Path) -> dict[str, int]:
        """
        Інгестія всіх DOCX файлів з директорії.

        Args:
            directory: Шлях до директорії з DOCX файлами.

        Returns:
            Словник {назва_файлу: кількість_чанків}.
        """
        results: dict[str, int] = {}

        docx_files = sorted(directory.glob("*.docx"))
        logger.info("starting_ingestion", files_found=len(docx_files))

        for file_path in docx_files:
            try:
                count = self.ingest_file(file_path)
                results[file_path.name] = count
            except RAGError as e:
                logger.error("ingestion_error", file=file_path.name, error=str(e))
                results[file_path.name] = 0

        total_chunks = sum(results.values())
        logger.info(
            "ingestion_complete",
            files_processed=len(results),
            total_chunks=total_chunks,
        )

        return results

    def _get_collection_count(self) -> int:
        """Отримання поточної кількості точок у колекції."""
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0
