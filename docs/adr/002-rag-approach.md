# ADR-002: RAG Approach

## Status
Accepted

## Context
Потрібна база знань з прикладів ТЗ для покращення якості генерації.

## Decision
- **Vector DB**: Qdrant (self-hosted через Docker)
- **Embeddings**: intfloat/multilingual-e5-large (1024 dimensions)
- **Chunking**: секція-aware розбиття з overlap
- **Caching**: in-memory lru_cache для ембедінгів

## Rationale
- Qdrant: простий setup, хороша продуктивність, безкоштовний
- multilingual-e5-large: найкраща підтримка української мови серед open-source моделей
- Section-aware chunking: зберігає контекст секцій КМУ №205
- In-memory cache: достатньо для MVP (<100 users)

## Consequences
- Потрібен Docker для Qdrant
- Модель ембедінгів ~1.3GB (завантаження при першому запуску)
- Cache втрачається при перезапуску (acceptable для MVP)
