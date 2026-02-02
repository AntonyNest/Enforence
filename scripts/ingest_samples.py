"""
Інгестія зразків ТЗ (DOCX) у Qdrant.

Обробляє 13 зразків ТЗ з директорії data/samples/.
"""

from pathlib import Path

from src.rag.ingestion import DocumentIngestionPipeline

SAMPLES_DIR = Path("data/samples")


def ingest_samples() -> None:
    """Обробка всіх DOCX зразків з data/samples/."""
    if not SAMPLES_DIR.exists():
        print(f"Директорія {SAMPLES_DIR} не знайдена!")
        print("Додайте DOCX файли зразків ТЗ у data/samples/")
        return

    docx_files = list(SAMPLES_DIR.glob("*.docx"))

    if not docx_files:
        print(f"DOCX файли не знайдено в {SAMPLES_DIR}")
        print("Додайте файли зразків ТЗ та запустіть повторно.")
        return

    print(f"Знайдено {len(docx_files)} DOCX файлів:")
    for f in docx_files:
        print(f"  - {f.name}")

    pipeline = DocumentIngestionPipeline()
    results = pipeline.ingest_directory(SAMPLES_DIR)

    print("\nРезультати інгестії:")
    print("-" * 50)
    for filename, chunks in results.items():
        status = "✓" if chunks > 0 else "✗"
        print(f"  {status} {filename}: {chunks} чанків")

    total = sum(results.values())
    print(f"\nЗагалом: {total} чанків з {len(results)} файлів")


if __name__ == "__main__":
    ingest_samples()
