"""
Тест підключення до MamayLM на RunPod.

Перевіряє доступність API та генерацію тексту.
"""

import asyncio

from src.config import settings
from src.llm.mamay_client import MamayLMClient


async def test_connection() -> None:
    """Перевірка підключення до MamayLM."""
    client = MamayLMClient()

    print(f"RunPod URL: {settings.mamay_llm_url}")
    print("Перевірка з'єднання...")

    # Health check
    is_healthy = await client.health_check()
    if is_healthy:
        print("✓ MamayLM доступний!")
    else:
        print("✗ MamayLM недоступний.")
        print("  Перевірте RunPod URL та чи запущений pod.")
        await client.close()
        return

    # Тест генерації
    print("\nТест генерації тексту...")
    try:
        response = await client.generate(
            prompt="Напиши короткий опис технічного завдання для веб-порталу.",
            system_prompt="Відповідай українською мовою.",
            temperature=0.7,
            max_tokens=200,
        )
        print(f"✓ Генерація успішна!")
        print(f"  Провайдер: {response.provider}")
        print(f"  Модель: {response.model}")
        print(f"  Токени: {response.tokens_used}")
        print(f"  Час: {response.duration_ms:.0f}ms")
        print(f"\n  Відповідь:\n  {response.text[:300]}...")
    except Exception as e:
        print(f"✗ Помилка генерації: {e}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_connection())
