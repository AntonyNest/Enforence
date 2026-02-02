# ADR-003: Agent Topology

## Status
Accepted

## Context
Потрібно визначити структуру та взаємодію AI агентів для генерації ТЗ.

## Decision
5 спеціалізованих агентів з послідовним пайплайном:

1. **RequirementsAnalyst** — аналіз та структурування вимог
2. **RAGRetriever** — пошук контексту з бази знань
3. **SectionGenerator** — генерація секцій (з паралелізмом)
4. **ComplianceChecker** — валідація КМУ №205
5. **DocumentAssembler** — збірка фінального документу

## Rationale
- Кожен агент має чітку відповідальність (SRP)
- SectionGenerator працює паралельно (asyncio.gather) для швидкості
- ComplianceChecker працює через Claude (reasoning capabilities)
- Target: ~120 секунд для повного ТЗ

## Consequences
- 5 агентів = 5 окремих LLM викликів мінімум
- Паралельна генерація секцій зменшує час
- Fallback логіка в кожному агенті через LLMRouter
