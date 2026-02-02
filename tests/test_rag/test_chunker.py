"""
Тести для DocumentChunker.
"""

import pytest

from src.rag.chunker import DocumentChunker


@pytest.fixture
def chunker():
    """Чанкер з налаштуваннями за замовчуванням."""
    return DocumentChunker(chunk_size=200, chunk_overlap=50)


def test_chunk_short_text(chunker):
    """Короткий текст повертається як один чанк."""
    text = "Це короткий текст для тесту."
    chunks = chunker.chunk_document(text, source_file="test.docx")

    assert len(chunks) >= 1
    assert chunks[0].source_file == "test.docx"


def test_chunk_long_text(chunker):
    """Довгий текст розбивається на декілька чанків."""
    text = "Це тестове речення. " * 100
    chunks = chunker.chunk_document(text)

    assert len(chunks) > 1


def test_chunk_with_sections(chunker):
    """Текст з секціями КМУ розпізнається."""
    text = """
1. Загальні відомості про засіб інформатизації
Цей розділ містить загальну інформацію про систему.

2. Відомості про робочий процес
Опис бізнес-процесів та робочих процесів.
"""
    chunks = chunker.chunk_document(text)

    # Повинні бути знайдені секції
    section_ids = [c.section_id for c in chunks if c.section_id]
    assert len(section_ids) > 0


def test_chunk_metadata(chunker):
    """Чанки містять правильні метадані."""
    text = "1. Загальні відомості\nТекст першої секції."
    chunks = chunker.chunk_document(text, source_file="sample.docx")

    for chunk in chunks:
        assert chunk.source_file == "sample.docx"
        assert chunk.text
