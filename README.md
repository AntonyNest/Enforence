# ENFORENCE

AI-платформа для автоматизованої генерації технічних завдань (ТЗ) згідно КМУ Постанова №205.

## Про проєкт

ENFORENCE скорочує час створення ТЗ з тижнів до 15-30 хвилин через multi-agent RAG architecture. Платформа генерує повні технічні завдання для державної сфери України з дотриманням нормативних вимог.

### Технічний стек

- **Backend:** FastAPI 0.104+ (async/await)
- **AI Orchestration:** CrewAI 0.28+ (multi-agent)
- **RAG:** LangChain 0.1+, Qdrant 1.7+
- **LLM:** MamayLM-Gemma-2-9B (Ukrainian, RunPod) + Claude Sonnet 4 (fallback)
- **Database:** SQLite (MVP) → PostgreSQL (production)
- **Export:** python-docx 1.1+

## Швидкий старт

### Передумови

- Python 3.11+
- Poetry
- Docker (для Qdrant)

### Встановлення

```bash
# 1. Клонування репозиторію
git clone https://github.com/AntonyNest/Enforence
cd Enforence

# 2. Встановлення залежностей
poetry install

# 3. Налаштування середовища
cp .env.example .env
# Відредагуйте .env: додайте RunPod URL та Anthropic API key

# 4. Запуск Qdrant
docker-compose up -d

# 5. Ініціалізація бази даних
poetry run python scripts/setup_db.py

# 6. Ініціалізація Qdrant колекції
poetry run python scripts/setup_qdrant.py

# 7. Інгестія зразків ТЗ (якщо є DOCX файли в data/samples/)
poetry run python scripts/ingest_samples.py

# 8. Тест підключення до MamayLM
poetry run python scripts/test_mamay.py

# 9. Запуск сервера
poetry run uvicorn src.main:app --reload

# 10. Перевірка
curl http://localhost:8000/health
```

## API Endpoints

| Метод | Endpoint | Опис |
|-------|----------|------|
| `GET` | `/health` | Перевірка стану сервісу |
| `POST` | `/api/v1/projects` | Створити проєкт |
| `GET` | `/api/v1/projects` | Список проєктів |
| `GET` | `/api/v1/projects/{id}` | Отримати проєкт |
| `POST` | `/api/v1/projects/{id}/generate` | Запустити генерацію ТЗ |
| `GET` | `/api/v1/projects/{id}/status` | Статус генерації |
| `GET` | `/api/v1/projects/{id}/document` | Отримати JSON документ |
| `PATCH` | `/api/v1/projects/{id}/sections/{sid}` | Редагувати секцію |
| `GET` | `/api/v1/projects/{id}/export/docx` | Завантажити DOCX |
| `GET` | `/api/v1/templates` | Шаблони КМУ |

Swagger UI доступний за адресою: `http://localhost:8000/docs`

## Архітектура

```
User Request → FastAPI → Generation Service
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
             Requirements  RAG      Section
              Analyst    Retriever  Generator
                              │         │
                              ▼         ▼
                           Qdrant    MamayLM/Claude
                              │         │
                    ┌─────────┘─────────┘
                    ▼
              Compliance Checker (Claude)
                    │
                    ▼
              Document Assembler
                    │
                    ▼
              DOCX Export
```

### LLM Стратегія

- **MamayLM**: генерація контенту українською (секції 1-10)
- **Claude**: compliance checking, валідація якості
- **Fallback**: Claude якщо MamayLM недоступний

## Тестування

```bash
# Всі тести
poetry run pytest

# З покриттям
poetry run pytest --cov=src --cov-report=html

# Конкретний модуль
poetry run pytest tests/test_api/ -v
```

## Структура КМУ №205

ТЗ складається з 10 розділів (8 обов'язкових + 2 опціональних):

1. Загальні відомості про засіб інформатизації
2. Відомості про робочий процес (бізнес-процеси)
3. Вимоги до засобу інформатизації
4. Склад та зміст робіт
5. Порядок контролю та приймання
6. Вимоги до підготовки до введення в дію
7. Умови використання
8. Вимоги до документування
9. Порядок внесення змін *(опціональний)*
10. Додатки *(опціональний)*

## Команда

- **Anton Nesterenko** — Backend, AI/ML
- **Марія Доненко** — Frontend (React/TypeScript)

## Ліцензія

Приватний проєкт. Всі права захищено.
