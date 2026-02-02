# ADR-001: LLM Strategy

## Status
Accepted

## Context
Потрібно обрати стратегію використання LLM для генерації ТЗ українською мовою.

## Decision
Гібридний підхід (Варіант B):
- **MamayLM-Gemma-2-9B**: генерація контенту українською (native training)
- **Claude Sonnet 4**: compliance checking (reasoning capabilities)
- **Fallback**: Claude якщо MamayLM недоступний

## Rationale
- MamayLM краще для української мови (native training on Ukrainian corpus)
- Claude краще для аналітичних задач (compliance, quality validation)
- Cost-effective: MamayLM на RunPod $0.59/hr vs Claude API calls
- Reliability: automatic fallback забезпечує безперебійну роботу

## Consequences
- Потрібен RunPod instance для MamayLM
- Два LLM провайдери = складніша інфраструктура
- Потрібен LLMRouter для маршрутизації
