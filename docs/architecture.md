# Архітектура ENFORENCE

## Огляд

ENFORENCE використовує multi-agent RAG архітектуру для генерації технічних завдань. Система складається з 5 спеціалізованих агентів, які працюють послідовно з елементами паралелізму.

## Компоненти

### 1. API Layer (FastAPI)
- RESTful API з автогенерацією OpenAPI spec
- CORS для фронтенду
- Dependency Injection через FastAPI Depends

### 2. Service Layer
- **ProjectService**: CRUD для проєктів
- **GenerationService**: оркестрація генерації ТЗ
- **DocumentService**: управління документами
- **ExportService**: конвертація у DOCX

### 3. Agent Layer (CrewAI)
- **RequirementsAnalyst**: збір та структурування вимог
- **RAGRetriever**: пошук релевантного контексту
- **SectionGenerator**: генерація секцій ТЗ
- **ComplianceChecker**: перевірка КМУ №205
- **DocumentAssembler**: збірка фінального документу

### 4. LLM Layer
- **MamayLMClient**: генерація українського контенту (RunPod)
- **ClaudeClient**: compliance checking (Anthropic API)
- **LLMRouter**: маршрутизація між провайдерами

### 5. RAG Pipeline
- **EmbeddingService**: multilingual-e5-large
- **DocumentChunker**: розбиття по секціях КМУ
- **DocumentIngestionPipeline**: DOCX → Qdrant
- **RAGRetriever**: семантичний пошук

### 6. Data Layer
- **SQLite**: проєкти, документи, задачі генерації
- **Qdrant**: векторна БД для RAG

## Потік даних

```
1. POST /projects → створення проєкту
2. POST /projects/{id}/generate → запуск генерації
   ├── RequirementsAnalyst → структуровані вимоги
   ├── RAGRetriever → контекст з бази знань
   ├── SectionGenerator × 10 → секції (parallel)
   ├── ComplianceChecker → оцінка відповідності
   └── DocumentAssembler → фінальний JSON
3. GET /projects/{id}/document → JSON ТЗ
4. GET /projects/{id}/export/docx → DOCX файл
```

## Масштабування

MVP використовує SQLite + in-memory cache. Для production:
- SQLite → PostgreSQL
- lru_cache → Redis
- Single instance → Docker Swarm / K8s
