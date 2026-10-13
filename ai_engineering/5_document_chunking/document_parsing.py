"""Parse local documents and split them into retrieval-friendly chunks."""

import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_document(file_path: str | Path) -> list[dict[str, Any]]:
	"""Load a PDF, DOCX, TXT, or Markdown file into text with source metadata.

	PDFs are returned one page at a time so page numbers remain available to
	downstream retrieval and citation code. Other supported files are one unit.
	"""
	path = Path(file_path)
	if not path.is_file():
		raise FileNotFoundError(f"Document not found: {path}")

	suffix = path.suffix.lower()
	if suffix == ".pdf":
		from pypdf import PdfReader

		reader = PdfReader(str(path))
		documents = []
		for page_number, page in enumerate(reader.pages, start=1):
			text = (page.extract_text() or "").strip()
			if text:
				documents.append(
					{
						"text": text,
						"metadata": {"source": str(path), "page": page_number},
					}
				)
		return documents

	if suffix == ".docx":
		from docx import Document

		word_document = Document(str(path))
		paragraphs = [paragraph.text.strip() for paragraph in word_document.paragraphs]
		text = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
	elif suffix in {".txt", ".md", ".markdown"}:
		text = path.read_text(encoding="utf-8-sig").strip()
	else:
		raise ValueError(
			f"Unsupported file type '{suffix}'. Supported types: PDF, DOCX, TXT, MD."
		)

	if not text:
		return []
	return [{"text": text, "metadata": {"source": str(path)}}]


def chunk_by_character(text: str, chunk_size: int, overlap: int) -> list[str]:
	"""Split fixed character windows; useful for predictable size limits.

	This is simple and reliable, but it may cut a sentence or word in half.
	"""
	_validate_chunk_settings(chunk_size, overlap)
	text = text.strip()
	if not text:
		return []

	chunks = []
	start = 0
	while start < len(text):
		end = min(start + chunk_size, len(text))
		chunks.append(text[start:end].strip())
		if end == len(text):
			break
		start = end - overlap
	return [chunk for chunk in chunks if chunk]


def chunk_by_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
	"""Prefer paragraph boundaries to keep related ideas together.

	Long paragraphs are split by character. Paragraphs preserve more context
	than fixed windows, but a short document may produce uneven chunk sizes.
	"""
	paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
	return _chunk_by_units(paragraphs, "\n\n", chunk_size, overlap)


def chunk_by_sentence(text: str, chunk_size: int, overlap: int) -> list[str]:
	"""Group sentences without splitting them unless one exceeds the limit.

	Sentence boundaries can make chunks easier to read, though abbreviations and
	unusual punctuation can confuse this lightweight sentence splitter.
	"""
	sentences = [
		sentence.strip()
		for sentence in re.split(r"(?<=[.!?])\s+|\n+", text.strip())
		if sentence.strip()
	]
	return _chunk_by_units(sentences, " ", chunk_size, overlap)


def chunk_by_word(text: str, chunk_size: int, overlap: int) -> list[str]:
	"""Split by word count, normalizing whitespace to single spaces.

	This is useful when reasoning about token-like limits, but word counts are
	not the same as model tokenizer token counts. Sizes and overlap are words.
	"""
	_validate_chunk_settings(chunk_size, overlap)
	words = re.findall(r"\S+", text)
	if not words:
		return []

	chunks = []
	step = chunk_size - overlap
	start = 0
	while start < len(words):
		end = min(start + chunk_size, len(words))
		chunks.append(" ".join(words[start:end]))
		if end == len(words):
			break
		start += step
	return chunks


def chunk_by_recursive(text: str, chunk_size: int, overlap: int) -> list[str]:
	"""Split using preferred separators, falling back to smaller boundaries.

	The order is paragraph, line, then word, and finally character. This usually
	keeps structure better than fixed windows while honoring a character limit.
	"""
	_validate_chunk_settings(chunk_size, overlap)
	text = text.strip()
	if not text:
		return []

	def split_recursively(value: str, separators: tuple[str, ...]) -> list[str]:
		if len(value) <= chunk_size:
			return [value]
		if not separators:
			return chunk_by_character(value, chunk_size, 0)

		separator = separators[0]
		pieces = value.split(separator)
		if len(pieces) == 1:
			return split_recursively(value, separators[1:])

		result = []
		current = ""
		for piece in pieces:
			if not piece:
				continue
			if len(piece) > chunk_size:
				if current:
					result.append(current)
					current = ""
				nested = split_recursively(piece, separators[1:])
				if result and separator and len(nested[0]) + len(separator) <= chunk_size:
					nested[0] = separator + nested[0]
				result.extend(nested)
				continue

			candidate = f"{current}{separator}{piece}" if current else piece
			if len(candidate) <= chunk_size:
				current = candidate
			else:
				if current:
					result.append(current)
				current = f"{separator}{piece}" if len(separator) + len(piece) <= chunk_size else piece

		if current:
			result.append(current)
		return result

	raw_chunks = split_recursively(text, ("\n\n", "\n", " "))
	chunks = []
	for raw_chunk in raw_chunks:
		if chunks and overlap:
			available_overlap = min(overlap, chunk_size - len(raw_chunk))
			if available_overlap > 0:
				raw_chunk = chunks[-1][-available_overlap:] + raw_chunk
		chunks.append(raw_chunk.strip())
	return [chunk for chunk in chunks if chunk]


def _chunk_by_units(
	units: list[str], separator: str, chunk_size: int, overlap: int
) -> list[str]:
	"""Pack text units and carry a small character overlap across boundaries."""
	_validate_chunk_settings(chunk_size, overlap)
	if not units:
		return []

	chunks = []
	current = ""
	carry = ""

	def emit_current() -> None:
		nonlocal current, carry
		if current.strip():
			current = current.strip()
			chunks.append(current)
			carry = current[-overlap:] if overlap else ""
			current = ""

	for unit in units:
		if len(unit) > chunk_size:
			emit_current()
			value = f"{carry}{separator}{unit}" if carry else unit
			oversized_chunks = chunk_by_character(value, chunk_size, overlap)
			chunks.extend(oversized_chunks)
			carry = oversized_chunks[-1][-overlap:] if overlap else ""
			continue

		prefix = current or carry
		candidate = f"{prefix}{separator}{unit}" if prefix else unit
		if len(candidate) > chunk_size:
			emit_current()
			available_overlap = max(0, chunk_size - len(unit) - len(separator))
			prefix = carry[-available_overlap:] if available_overlap else ""
			candidate = f"{prefix}{separator}{unit}" if prefix else unit
		current = candidate
		carry = ""

	emit_current()
	return chunks


def chunk_documents(
	documents: list[dict[str, Any]],
	chunk_size: int = 1000,
	overlap: int = 150,
	method: str = "paragraph",
) -> list[dict[str, Any]]:
	"""Chunk parsed documents and retain source metadata for each chunk."""
	chunkers = {
		"character": chunk_by_character,
		"paragraph": chunk_by_paragraph,
		"sentence": chunk_by_sentence,
		"word": chunk_by_word,
		"recursive": chunk_by_recursive,
	}
	if method not in chunkers:
		raise ValueError(f"method must be one of: {', '.join(chunkers)}")

	chunked_documents = []
	for document in documents:
		text_chunks = chunkers[method](document["text"], chunk_size, overlap)
		for chunk_index, text in enumerate(text_chunks):
			chunked_documents.append(
				{
					"text": text,
					"metadata": {
						**document.get("metadata", {}),
						"chunk_index": chunk_index,
					},
				}
			)
	return chunked_documents


def _validate_chunk_settings(chunk_size: int, overlap: int) -> None:
	if chunk_size <= 0:
		raise ValueError("chunk_size must be greater than zero")
	if overlap < 0 or overlap >= chunk_size:
		raise ValueError("overlap must be at least zero and smaller than chunk_size")


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("file", help="Path to a PDF, DOCX, TXT, or Markdown file")
	parser.add_argument(
		"--method",
		choices=("character", "paragraph", "sentence", "word", "recursive"),
		default="paragraph",
		help="Chunking strategy (default: paragraph)",
	)
	parser.add_argument("--chunk-size", type=int, default=1000)
	parser.add_argument("--overlap", type=int, default=150)
	args = parser.parse_args()

	documents = parse_document(args.file)
	chunks = chunk_documents(
		documents,
		chunk_size=args.chunk_size,
		overlap=args.overlap,
		method=args.method,
	)
	print(json.dumps(chunks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
