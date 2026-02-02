"""
Ініціалізація Qdrant колекції для RAG.

Створює колекцію з налаштуваннями для multilingual-e5-large.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.config import settings


def setup_qdrant() -> None:
    """Створення колекції у Qdrant."""
    client = QdrantClient(url=settings.qdrant_url)

    collections = client.get_collections().collections
    existing_names = [c.name for c in collections]

    if settings.qdrant_collection in existing_names:
        print(f"Колекція '{settings.qdrant_collection}' вже існує.")
        info = client.get_collection(settings.qdrant_collection)
        print(f"Кількість точок: {info.points_count}")
        return

    # Розмірність multilingual-e5-large = 1024
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE,
        ),
    )

    print(f"Колекція '{settings.qdrant_collection}' створена успішно!")
    print(f"Розмірність векторів: 1024 (multilingual-e5-large)")
    print(f"Метрика: Cosine Similarity")


if __name__ == "__main__":
    setup_qdrant()
