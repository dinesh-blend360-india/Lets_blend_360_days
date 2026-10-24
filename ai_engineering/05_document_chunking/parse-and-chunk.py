"""Parse local documents and create structure-aware, retrieval-friendly chunks.

Supported formats: PDF, DOCX, TXT, Markdown.

Day 05 improvements:
- Prefer paragraph/sentence/list/table boundaries over arbitrary character windows.
- Carry Markdown/DOCX heading context into chunk text and metadata.
- Preserve Markdown and DOCX tables as table-like text; repeat table headers when splitting.
- Retain source, page (when available), section, chunk index, and content type.
- Use character-based overlap consistently and report overlap metadata.

Install optional readers as needed:
    pip install pypdf python-docx

Example:
    python chunking_day05.py handbook.md --chunk-size 1000 --overlap 120 --quality-report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable


HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'“‘(\[]?[A-Z0-9])|\n+")


def parse_document(file_path: str | Path) -> list[dict[str, Any]]:
    """Load PDF, DOCX, TXT, or Markdown and retain available source metadata.

    PDFs are returned as one document unit per page so page metadata survives.
    DOCX tables are rendered to Markdown-like tables and heading styles become
    Markdown headings, allowing the same structural chunker to handle them.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("Reading PDFs requires pypdf. Install it with: pip install pypdf") from exc

        reader = PdfReader(str(path))
        documents: list[dict[str, Any]] = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                documents.append({"text": page_text, "metadata": {"source": str(path), "page": page_number}})
        return documents

    if suffix == ".docx":
        try:
            from docx import Document
            from docx.oxml.table import CT_Tbl
            from docx.oxml.text.paragraph import CT_P
            from docx.table import Table
            from docx.text.paragraph import Paragraph
        except ImportError as exc:
            raise ImportError("Reading DOCX files requires python-docx. Install it with: pip install python-docx") from exc

        word_document = Document(str(path))
        pieces: list[str] = []
        # Iterate body children in document order so tables are not silently lost.
        for child in word_document.element.body.iterchildren():
            if isinstance(child, CT_P):
                paragraph = Paragraph(child, word_document)
                value = paragraph.text.strip()
                if not value:
                    continue
                style_name = getattr(paragraph.style, "name", "") or ""
                match = re.match(r"Heading\s+(\d+)", style_name, flags=re.IGNORECASE)
                if match:
                    level = min(6, max(1, int(match.group(1))))
                    pieces.append(f"{'#' * level} {value}")
                else:
                    pieces.append(value)
            elif isinstance(child, CT_Tbl):
                table = Table(child, word_document)
                rows = [[cell.text.strip().replace("\n", " / ") for cell in row.cells] for row in table.rows]
                if not rows:
                    continue
                width = max(len(row) for row in rows)
                rows = [row + [""] * (width - len(row)) for row in rows]
                header = rows[0]
                divider = ["---"] * width
                table_lines = ["| " + " | ".join(_escape_table_cell(c) for c in header) + " |",
                               "| " + " | ".join(divider) + " |"]
                table_lines.extend("| " + " | ".join(_escape_table_cell(c) for c in row) + " |" for row in rows[1:])
                pieces.append("\n".join(table_lines))
        text = "\n\n".join(pieces).strip()
    elif suffix in {".txt", ".md", ".markdown"}:
        text = path.read_text(encoding="utf-8-sig").strip()
    else:
        raise ValueError(f"Unsupported file type '{suffix}'. Supported file types: PDF, DOCX, TXT, MD.")

    if not text:
        return []
    return [{"text": text, "metadata": {"source": str(path)}}]


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").strip()


def _validate_chunk_settings(chunk_size: int, overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be at least zero and smaller than chunk_size")


def _word_boundary_end(text: str, start: int, proposed_end: int) -> int:
    """Move a cut to a nearby whitespace boundary without making a tiny chunk."""
    end = min(proposed_end, len(text))
    if end >= len(text):
        return end
    floor = start + max(1, (end - start) // 2)
    boundary = text.rfind(" ", floor, end)
    if boundary > start:
        return boundary
    boundary = text.find(" ", end, min(len(text), end + 80))
    return boundary if boundary != -1 else end


def _overlap_tail(text: str, overlap: int) -> str:
    """Return a useful suffix near the requested character overlap."""
    if overlap <= 0 or not text:
        return ""
    tail = text[-overlap:]
    # Prefer starting at a word boundary, but do not discard nearly all context.
    first_space = tail.find(" ")
    if 0 <= first_space < len(tail) // 2:
        tail = tail[first_space + 1:]
    return tail.strip()


def chunk_by_character(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into character windows, preferring word boundaries."""
    _validate_chunk_settings(chunk_size, overlap)
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = _word_boundary_end(text, start, start + chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        next_start = max(start + 1, end - overlap)
        # Do not start in the middle of a word when an easy boundary is available.
        next_space = text.find(" ", next_start, min(len(text), next_start + 80))
        if next_space != -1 and next_space - next_start < 40:
            next_start = next_space + 1
        start = next_start
    return chunks


def _split_sentences(text: str) -> list[str]:
    """Lightweight sentence splitter; intentionally dependency-free."""
    # Keep line breaks as boundaries, while not splitting on punctuation without
    # following whitespace. This is still heuristic (e.g. abbreviations can vary).
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text.strip()) if part.strip()]


def _pack_units(units: Iterable[str], chunk_size: int, overlap: int, separator: str = " ") -> list[str]:
    """Pack complete units into chunks, carrying character overlap between them."""
    _validate_chunk_settings(chunk_size, overlap)
    result: list[str] = []
    current = ""
    for raw_unit in units:
        unit = raw_unit.strip()
        if not unit:
            continue
        if len(unit) > chunk_size:
            if current:
                result.append(current.strip())
                current = _overlap_tail(current, overlap)
            long_pieces = chunk_by_character(unit, chunk_size, overlap)
            if long_pieces:
                result.extend(long_pieces[:-1])
                current = long_pieces[-1]
            continue
        candidate = f"{current}{separator}{unit}" if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                result.append(current.strip())
            prefix = _overlap_tail(current, overlap)
            if prefix and len(prefix) + len(separator) + len(unit) <= chunk_size:
                current = f"{prefix}{separator}{unit}"
            else:
                current = unit
    if current.strip():
        result.append(current.strip())
    return result


def chunk_by_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Pack paragraphs together while keeping paragraph boundaries when possible."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    output: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = _split_sentences(paragraph) if len(paragraph) > chunk_size else [paragraph]
        for piece in pieces:
            if len(piece) > chunk_size:
                if current:
                    output.append(current)
                    current = _overlap_tail(current, overlap)
                split_pieces = chunk_by_character(piece, chunk_size, overlap)
                output.extend(split_pieces[:-1])
                current = split_pieces[-1] if split_pieces else ""
                continue
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    output.append(current)
                prefix = _overlap_tail(current, overlap)
                current = f"{prefix}\n\n{piece}" if prefix and len(prefix) + len(piece) + 2 <= chunk_size else piece
    if current.strip():
        output.append(current.strip())
    return output


def chunk_by_sentence(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Pack full sentences together where possible."""
    sentences = _split_sentences(text)
    return _pack_units(sentences, chunk_size, overlap, separator=" ")


def chunk_by_word(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split on word boundaries; chunk_size and overlap are still character counts."""
    words = re.findall(r"\S+", text.strip())
    if not words:
        return []
    return _pack_units(words, chunk_size, overlap, separator=" ")


def chunk_by_recursive(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split on paragraphs, then lines, sentences/words, and finally characters."""
    _validate_chunk_settings(chunk_size, overlap)
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        return chunk_by_paragraph(text, chunk_size, overlap)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        return _pack_units(lines, chunk_size, overlap, separator="\n")
    sentences = _split_sentences(text)
    if len(sentences) > 1:
        return _pack_units(sentences, chunk_size, overlap, separator=" ")
    words = re.findall(r"\S+", text)
    if len(words) > 1:
        return _pack_units(words, chunk_size, overlap, separator=" ")
    return chunk_by_character(text, chunk_size, overlap)


def _is_table_line(line: str) -> bool:
    line = line.strip()
    return "|" in line and (line.startswith("|") or line.count("|") >= 2)


def _is_list_line(line: str) -> bool:
    return bool(LIST_RE.match(line))


def _extract_blocks(text: str, page: int | None = None) -> list[dict[str, Any]]:
    """Parse a text page into heading, paragraph, list, and table blocks."""
    lines = text.splitlines()
    blocks: list[dict[str, Any]] = []
    buffer: list[str] = []
    buffer_type = "paragraph"

    def flush() -> None:
        nonlocal buffer, buffer_type
        value = "\n".join(buffer).strip()
        if value:
            block: dict[str, Any] = {"text": value, "content_type": buffer_type}
            if page is not None:
                block["page"] = page
            blocks.append(block)
        buffer = []
        buffer_type = "paragraph"

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush()
            i += 1
            continue

        heading_match = HEADING_RE.match(line)
        # Also recognize simple Markdown Setext headings (underlined title).
        if i + 1 < len(lines) and re.match(r"^\s*(?:===+|---+)\s*$", lines[i + 1]) and not _is_table_line(line):
            flush()
            level = 1 if "=" in lines[i + 1] else 2
            heading = {"text": stripped, "content_type": "heading", "level": level}
            if page is not None:
                heading["page"] = page
            blocks.append(heading)
            i += 2
            continue
        if heading_match:
            flush()
            heading = {"text": heading_match.group(2).strip(), "content_type": "heading", "level": len(heading_match.group(1))}
            if page is not None:
                heading["page"] = page
            blocks.append(heading)
            i += 1
            continue

        if _is_table_line(line):
            flush()
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip() and _is_table_line(lines[i]):
                table_lines.append(lines[i].strip())
                i += 1
            block = {"text": "\n".join(table_lines), "content_type": "table"}
            if page is not None:
                block["page"] = page
            blocks.append(block)
            continue

        if _is_list_line(line):
            flush()
            list_lines: list[str] = []
            while i < len(lines) and lines[i].strip():
                if _is_list_line(lines[i]) or lines[i].startswith((" ", "\t")):
                    list_lines.append(lines[i].rstrip())
                    i += 1
                else:
                    break
            block = {"text": "\n".join(list_lines).strip(), "content_type": "list"}
            if page is not None:
                block["page"] = page
            blocks.append(block)
            continue

        if buffer and buffer_type != "paragraph":
            flush()
        buffer_type = "paragraph"
        buffer.append(line.rstrip())
        i += 1

    flush()
    return blocks


def _parse_table_rows(table_text: str) -> list[str]:
    return [line.strip() for line in table_text.splitlines() if _is_table_line(line)]


def _split_table(table_text: str, chunk_size: int) -> list[str]:
    """Split oversized Markdown-like tables by rows and repeat their header."""
    lines = _parse_table_rows(table_text)
    if len(table_text) <= chunk_size:
        return [table_text.strip()]

    if len(lines) <= 2:
        # There is no safe row-level grouping to preserve. Split the complete
        # table as a bounded character fallback rather than emitting an
        # oversized chunk.
        return chunk_by_character(table_text, chunk_size, 0)

    header = lines[0]
    has_separator = bool(re.match(r"^\|?\s*:?-{3,}", lines[1].lstrip("| ")))
    separator = lines[1] if has_separator else None
    data_rows = lines[2:] if has_separator else lines[1:]
    prefix = [header] + ([separator] if separator else [])
    groups: list[str] = []
    current = prefix[:]
    for row in data_rows:
        # A single row can be larger than the configured limit. It cannot be
        # kept as one table row, so fall back to bounded text pieces.
        if len(row) > chunk_size:
            if len(current) > len(prefix):
                groups.append("\n".join(current))
                current = prefix[:]
            groups.extend(chunk_by_character(row, chunk_size, 0))
            continue

        candidate = "\n".join(current + [row])
        if len(candidate) <= chunk_size:
            current.append(row)
        else:
            if len(current) > len(prefix):
                groups.append("\n".join(current))
            # Preserve the header only when it leaves room for this row.
            if len("\n".join(prefix + [row])) <= chunk_size:
                current = prefix[:] + [row]
            else:
                groups.extend(chunk_by_character(row, chunk_size, 0))
                current = prefix[:]
    if current:
        groups.append("\n".join(current))
    return groups


def _split_list(text: str, chunk_size: int) -> list[str]:
    """Split long lists at item boundaries instead of slicing through items."""
    items = text.splitlines()
    groups: list[str] = []
    current: list[str] = []
    for item in items:
        candidate = "\n".join(current + [item])
        if current and len(candidate) > chunk_size:
            groups.append("\n".join(current))
            current = [item]
        else:
            current.append(item)
    if current:
        groups.append("\n".join(current))
    output: list[str] = []
    for group in groups:
        if len(group) > chunk_size:
            output.extend(chunk_by_recursive(group, chunk_size, 0))
        else:
            output.append(group)
    return output


def _split_long_paragraph(text: str, chunk_size: int) -> list[str]:
    """Split oversized prose by sentence first, then word/character as needed."""
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        words = re.findall(r"\S+", text)
        if len(words) > 1:
            return _pack_units(words, chunk_size, 0, separator=" ")
        return chunk_by_character(text, chunk_size, 0)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_split_long_paragraph(sentence, chunk_size))
            continue
        candidate = f"{current} {sentence}" if current else sentence
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 1000,
    overlap: int = 150,
    method: str = "structure",
) -> list[dict[str, Any]]:
    """Create structure-aware chunks, preserving source and heading metadata.

    ``chunk_size`` and ``overlap`` are measured in characters for all methods.
    The ``structure`` method is recommended for Day 05 quality tests.
    """
    _validate_chunk_settings(chunk_size, overlap)
    allowed = {"structure", "character", "paragraph", "sentence", "word", "recursive"}
    if method not in allowed:
        raise ValueError(f"method must be one of: {', '.join(sorted(allowed))}")

    # The character/paragraph/sentence/word/recursive modes are deliberately
    # raw text baselines. They must not pass through heading/table parsing.
    if method != "structure":
        splitters = {
            "character": chunk_by_character,
            "paragraph": chunk_by_paragraph,
            "sentence": chunk_by_sentence,
            "word": chunk_by_word,
            "recursive": chunk_by_recursive,
        }
        output: list[dict[str, Any]] = []
        for document_index, document in enumerate(documents):
            metadata = dict(document.get("metadata", {}))
            text_chunks = splitters[method](str(document.get("text", "")), chunk_size, overlap)
            for chunk_index, text in enumerate(text_chunks):
                output.append({
                    "text": text,
                    "metadata": {
                        **metadata,
                        "chunk_index": chunk_index,
                        "content_type": "raw",
                        "overlap_chars": overlap if chunk_index else 0,
                    },
                })
        return _finalize_chunks(output)

    # Group PDF pages by source so heading context can continue over a page break.
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for index, document in enumerate(documents):
        metadata = dict(document.get("metadata", {}))
        source_key = str(metadata.get("source", f"__document_{index}"))
        groups.setdefault(source_key, []).append(document)

    def split_oversized_text(value: str, max_size: int | None = None) -> list[str]:
        """Apply the requested splitter to oversized prose without double overlap."""
        limit = max_size or chunk_size
        if method == "structure":
            return _split_long_paragraph(value, limit)
        splitters = {
            "character": chunk_by_character,
            "paragraph": chunk_by_paragraph,
            "sentence": chunk_by_sentence,
            "word": chunk_by_word,
            "recursive": chunk_by_recursive,
        }
        return splitters[method](value, limit, 0)

    output: list[dict[str, Any]] = []
    for source_key, source_docs in groups.items():
        source_docs = sorted(source_docs, key=lambda d: d.get("metadata", {}).get("page", 0) or 0)
        first_metadata = dict(source_docs[0].get("metadata", {}))
        heading_stack: list[tuple[int, str]] = []
        current_text = ""
        current_heading = ""
        current_types: list[str] = []
        current_pages: list[int] = []
        current_overlap_chars = 0
        source_chunk_index = 0

        def context_prefix(heading_path: str) -> str:
            if not heading_path:
                return ""
            prefix = f"Section: {heading_path}\n\n"
            # Keep a long section path useful without allowing it to consume the chunk.
            max_prefix = max(24, min(120, chunk_size // 5))
            if len(prefix) > max_prefix:
                # Prefer the meaningful leaf heading in chunk text; the complete
                # hierarchy remains available in metadata['heading_path'].
                leaf_heading = heading_path.split(" > ")[-1]
                prefix = f"Section: {leaf_heading}\n\n"
                if len(prefix) > max_prefix:
                    available = max(1, max_prefix - len("Section: …\n\n"))
                    prefix = f"Section: …{leaf_heading[-available:]}\n\n"
            return prefix if len(prefix) < chunk_size else ""

        def text_limit(heading_path: str) -> int:
            return max(1, chunk_size - len(context_prefix(heading_path)))

        def make_text(body: str, heading_path: str) -> str:
            return f"{context_prefix(heading_path)}{body.strip()}"

        def emit(body: str | None = None, *, heading_path: str | None = None,
                 content_types: list[str] | None = None, pages: list[int] | None = None,
                 overlap_chars: int = 0) -> None:
            nonlocal source_chunk_index
            value = (body if body is not None else current_text).strip()
            if not value:
                return
            path_value = current_heading if heading_path is None else heading_path
            types_value = current_types if content_types is None else content_types
            pages_value = current_pages if pages is None else pages
            metadata = {k: v for k, v in first_metadata.items() if k not in {"page"}}
            metadata.update({
                "chunk_index": source_chunk_index,
                "heading_path": path_value,
                "content_type": types_value[0] if len(set(types_value)) == 1 and types_value else ("mixed" if types_value else "paragraph"),
                "overlap_chars": overlap_chars,
            })
            clean_pages = sorted(set(pages_value))
            if clean_pages:
                metadata["page_start"] = clean_pages[0]
                metadata["page_end"] = clean_pages[-1]
                if len(clean_pages) == 1:
                    metadata["page"] = clean_pages[0]
            output.append({"text": make_text(value, path_value), "metadata": metadata})
            source_chunk_index += 1

        def flush(*, keep_overlap: bool = False) -> str:
            nonlocal current_text, current_types, current_pages, current_overlap_chars
            old_text = current_text.strip()
            if old_text:
                emit(old_text, overlap_chars=current_overlap_chars)
            tail_size = min(overlap, max(0, text_limit(current_heading) // 3))
            tail = _overlap_tail(old_text, tail_size) if keep_overlap else ""
            current_text = tail
            current_types = ["paragraph"] if tail else []
            current_pages = list(current_pages[-1:]) if tail and current_pages else []
            current_overlap_chars = len(tail)
            return tail

        def add_prose(unit: str, page: int | None, content_type: str = "paragraph") -> None:
            nonlocal current_text, current_heading, current_types, current_pages, current_overlap_chars
            unit = unit.strip()
            if not unit:
                return
            limit = text_limit(current_heading)
            if len(unit) > limit:
                pieces = split_oversized_text(unit, limit)
                for piece in pieces:
                    add_prose(piece, page, content_type)
                return
            separator = "\n\n" if current_text else ""
            candidate = current_text + separator + unit
            if current_text and len(candidate) > limit:
                flush(keep_overlap=True)
                limit = text_limit(current_heading)
                separator = "\n\n" if current_text else ""
                # Reserve room for the actual unit. If needed, discard overlap rather
                # than exceed the configured output chunk size.
                if len(current_text) + len(separator) + len(unit) > limit:
                    current_text = ""
                    current_types = []
                    current_pages = []
                    current_overlap_chars = 0
                    separator = ""
                candidate = current_text + separator + unit
            current_text = candidate
            current_types.append(content_type)
            if page is not None:
                current_pages.append(page)

        for document in source_docs:
            page_value = document.get("metadata", {}).get("page")
            try:
                page_number = int(page_value) if page_value is not None else None
            except (TypeError, ValueError):
                page_number = None
            blocks = _extract_blocks(str(document.get("text", "")), page_number)
            for block in blocks:
                block_type = block["content_type"]
                block_text = block["text"].strip()
                if block_type == "heading":
                    # A heading starts a new semantic section; don't overlap across it.
                    flush(keep_overlap=False)
                    level = int(block.get("level", 1))
                    heading_stack = [(lvl, name) for lvl, name in heading_stack if lvl < level]
                    heading_stack.append((level, block_text))
                    current_heading = " > ".join(name for _, name in heading_stack)
                    continue

                section_path = " > ".join(name for _, name in heading_stack)
                if current_text and section_path != current_heading:
                    flush(keep_overlap=False)
                current_heading = section_path

                if block_type == "table":
                    flush(keep_overlap=False)
                    table_pieces = _split_table(block_text, text_limit(section_path))
                    for table_piece in table_pieces:
                        emit(table_piece, heading_path=section_path, content_types=["table"],
                             pages=[page_number] if page_number is not None else [], overlap_chars=0)
                    continue

                if block_type == "list":
                    flush(keep_overlap=False)
                    list_pieces = _split_list(block_text, text_limit(section_path))
                    for list_piece in list_pieces:
                        emit(list_piece, heading_path=section_path, content_types=["list"],
                             pages=[page_number] if page_number is not None else [], overlap_chars=0)
                    continue

                # Keep ordinary short paragraphs whole. Only oversized paragraphs are
                # sentence-split so a multi-sentence rule is not arbitrarily severed.
                if len(block_text) <= text_limit(section_path):
                    add_prose(block_text, page_number)
                else:
                    flush(keep_overlap=False)
                    pieces = split_oversized_text(block_text, text_limit(section_path))
                    for piece_index, piece in enumerate(pieces):
                        if piece_index == 0:
                            add_prose(piece, page_number)
                        else:
                            # Force a boundary; add_prose will create controlled overlap
                            # when the next piece does not fit in the current chunk.
                            add_prose(piece, page_number)
            # Don't force a flush at each PDF page: text/heading context may continue.

        flush(keep_overlap=False)

    return _finalize_chunks(output)


def _finalize_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add stable IDs and a global index after all chunking is complete."""
    seen: set[str] = set()
    for index, chunk in enumerate(chunks):
        metadata = chunk.setdefault("metadata", {})
        source = str(metadata.get("source", ""))
        page = str(metadata.get("page", metadata.get("page_start", "")))
        basis = "|".join((source, page, str(metadata.get("chunk_index", index)), chunk.get("text", "")))
        chunk_id = "chunk_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]
        if chunk_id in seen:
            raise ValueError(f"Duplicate chunk_id generated: {chunk_id}")
        seen.add(chunk_id)
        metadata["chunk_id"] = chunk_id
        metadata["global_chunk_index"] = index
    return chunks


def validate_chunks(
    chunks: list[dict[str, Any]],
    *,
    chunk_size: int,
) -> dict[str, Any]:
    """Validate invariants required before embedding."""
    errors: list[str] = []
    ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        text = str(chunk.get("text", ""))
        metadata = chunk.get("metadata") or {}
        chunk_id = metadata.get("chunk_id")
        if not text.strip():
            errors.append(f"chunk {index} is empty")
        if not metadata.get("source"):
            errors.append(f"chunk {index} is missing metadata.source")
        if not chunk_id:
            errors.append(f"chunk {index} is missing metadata.chunk_id")
        elif chunk_id in ids:
            errors.append(f"duplicate chunk_id: {chunk_id}")
        else:
            ids.add(str(chunk_id))
        if len(text) > chunk_size:
            errors.append(f"chunk {index} exceeds {chunk_size} characters ({len(text)})")
    if errors:
        raise ValueError("Chunk validation failed: " + "; ".join(errors))
    return {
        "valid": True,
        "chunk_count": len(chunks),
        "unique_chunk_ids": len(ids),
        "max_text_chars": max((len(str(c.get("text", ""))) for c in chunks), default=0),
    }


def analyze_chunk_quality(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return basic measurable diagnostics for the Day 05 manual review."""
    sizes = [len(str(chunk.get("text", ""))) for chunk in chunks]
    metadata_items = [chunk.get("metadata", {}) for chunk in chunks]
    return {
        "chunk_count": len(chunks),
        "chunk_size_chars": {
            "min": min(sizes) if sizes else 0,
            "max": max(sizes) if sizes else 0,
            "average": round(sum(sizes) / len(sizes), 2) if sizes else 0,
        },
        "chunks_with_source": sum(bool(meta.get("source")) for meta in metadata_items),
        "chunks_with_heading_context": sum(bool(meta.get("heading_path")) for meta in metadata_items),
        "chunks_with_page_location": sum("page" in meta or "page_start" in meta for meta in metadata_items),
        "content_type_counts": {
            content_type: sum(meta.get("content_type") == content_type for meta in metadata_items)
            for content_type in sorted({meta.get("content_type", "unknown") for meta in metadata_items})
        },
        "recorded_overlap_chars": sum(int(meta.get("overlap_chars", 0) or 0) for meta in metadata_items),
        "note": "This report checks measurable metadata/size properties. Boundary meaning, heading relevance, small details, and table semantics still require the six manual test cases.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Path to a PDF, DOCX, TXT, or Markdown file")
    parser.add_argument(
        "--method",
        choices=("structure", "character", "paragraph", "sentence", "word", "recursive"),
        default="structure",
        help="Chunking strategy (default: structure-aware)",
    )
    parser.add_argument("--chunk-size", type=int, default=1000, help="Maximum chunk body size in characters")
    parser.add_argument("--overlap", type=int, default=150, help="Target overlap in characters")
    parser.add_argument("--quality-report", action="store_true", help="Include basic Day 05 diagnostics in the JSON output")
    parser.add_argument(
        "--output",
        help="JSON output path (default: <input-name>-chunked.json beside the input document)",
    )
    args = parser.parse_args()

    input_path = Path(args.file)
    method_label = "structure" if args.method == "structure" else args.method
    output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}-{method_label}-chunked.json")

    documents = parse_document(input_path)
    chunks = chunk_documents(documents, chunk_size=args.chunk_size, overlap=args.overlap, method=args.method)
    validation = validate_chunks(chunks, chunk_size=args.chunk_size)
    result: Any = {
        "experiment": {
            "method": args.method,
            "chunk_size_chars": args.chunk_size,
            "overlap_chars": args.overlap,
            "source_document": str(input_path),
        },
        "validation": validation,
        "chunks": chunks,
    }
    if args.quality_report:
        result["quality_report"] = analyze_chunk_quality(chunks)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(chunks)} chunks to: {output_path}")
    print(f"Validation: {validation['unique_chunk_ids']} unique chunk IDs; max size {validation['max_text_chars']} characters")
    if args.quality_report:
        report = result["quality_report"]
        print(f"Quality report: {report['chunk_count']} chunks; max chunk size {report['chunk_size_chars']['max']} characters")


if __name__ == "__main__":
    main()
