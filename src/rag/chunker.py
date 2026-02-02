"""
Розбиття тексту на семантичні чанки для RAG.

Оптимізовано для документів ТЗ українською мовою.
"""

import re
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """Чанк тексту з метаданими."""

    text: str
    section_id: str | None = None
    section_title: str | None = None
    source_file: str | None = None
    chunk_index: int = 0


class DocumentChunker:
    """
    Розбиття документів ТЗ на семантичні чанки.

    Враховує структуру КМУ №205 (секції, підсекції).
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        text: str,
        source_file: str | None = None,
    ) -> list[TextChunk]:
        """
        Розбиття повного документу ТЗ на чанки.

        Args:
            text: Повний текст документу.
            source_file: Назва файлу-джерела.

        Returns:
            Список TextChunk з метаданими.
        """
        # Спроба розбити по секціях ТЗ
        sections = self._split_by_sections(text)

        chunks: list[TextChunk] = []
        for section_id, section_title, section_text in sections:
            section_chunks = self._split_text(section_text)
            for i, chunk_text in enumerate(section_chunks):
                chunks.append(
                    TextChunk(
                        text=chunk_text.strip(),
                        section_id=section_id,
                        section_title=section_title,
                        source_file=source_file,
                        chunk_index=i,
                    )
                )

        logger.info(
            "document_chunked",
            source=source_file,
            total_chunks=len(chunks),
            sections_found=len(sections),
        )

        return chunks

    def _split_by_sections(
        self, text: str
    ) -> list[tuple[str | None, str | None, str]]:
        """
        Розбиття тексту по секціях КМУ №205.

        Шукає патерни виду "1. Загальні відомості", "2.1. Опис процесів", тощо.
        """
        # Патерн для заголовків секцій (1. Назва, 2.1. Назва, тощо)
        section_pattern = re.compile(
            r"^(\d+\.?\d*\.?)\s+(.+?)$",
            re.MULTILINE,
        )

        matches = list(section_pattern.finditer(text))

        if not matches:
            # Якщо секцій не знайдено — повертаємо весь текст
            return [(None, None, text)]

        sections = []
        for i, match in enumerate(matches):
            section_id = match.group(1).rstrip(".")
            section_title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            if section_text:
                sections.append((section_id, section_title, section_text))

        return sections

    def _split_text(self, text: str) -> list[str]:
        """
        Розбиття тексту на чанки з перекриттям.

        Args:
            text: Текст для розбиття.

        Returns:
            Список чанків.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Шукаємо кінець речення для чистого розрізу
            if end < len(text):
                # Шукаємо крапку, знак питання або оклику
                for sep in [". ", ".\n", "? ", "! ", "\n\n"]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap

        return chunks
