from rag.context_builder import build_context


def result(chunk_id="chunk_1", text="Original evidence", **metadata):
    return {
        "rank": metadata.pop("rank", 1),
        "similarity": metadata.pop("similarity", 0.82),
        "chunk_id": chunk_id,
        "text": text,
        "metadata": metadata,
    }


def test_one_chunk_is_formatted_and_preserved():
    built = build_context("question", [result(source="policy.md", heading_path="Travel", page=2)])
    assert len(built.evidence) == 1
    assert built.evidence[0].chunk_id == "chunk_1"
    assert built.evidence[0].text == "Original evidence"
    assert "[EVIDENCE]" in built.formatted_context
    assert "[/EVIDENCE]" in built.formatted_context
    assert "rank: 1" in built.formatted_context
    assert "similarity: 0.8200" in built.formatted_context


def test_multiple_chunks_preserve_order_and_metadata():
    built = build_context("question", [
        result("chunk_a", "A", source="a.md", heading_path="A", page_start=1, page_end=2),
        result("chunk_b", "B", source="b.md", heading_path="B", page=4, rank=2),
    ])
    assert [item.chunk_id for item in built.evidence] == ["chunk_a", "chunk_b"]
    assert built.evidence[0].page == "1-2"
    assert built.evidence[1].metadata["source"] == "b.md"
    assert built.formatted_context.index("chunk_a") < built.formatted_context.index("chunk_b")


def test_missing_optional_metadata_is_explicit_not_invented():
    built = build_context("question", [result("chunk_missing", "Text", source="known.md")])
    assert built.evidence[0].section == "not available"
    assert built.evidence[0].page == "not available"
    assert "source: known.md" in built.formatted_context
    assert "section: not available" in built.formatted_context
    assert "page: not available" in built.formatted_context


def test_empty_results_return_empty_context():
    built = build_context("question", [])
    assert built.formatted_context == ""
    assert built.evidence == []
    assert built.excluded == []


def test_budget_excludes_whole_block_and_records_reason():
    first = result("chunk_keep", "keep this", source="a.md")
    second = result("chunk_exclude", "exclude this", source="b.md")
    one = build_context("question", [first])
    built = build_context("question", [first, second], max_context_chars=one.used_context_chars + 1)
    assert [item.chunk_id for item in built.evidence] == ["chunk_keep"]
    assert built.excluded[0].chunk_id == "chunk_exclude"
    assert "context budget" in built.excluded[0].reason
    assert "exclude this" not in built.formatted_context


def test_only_supplied_chunks_appear_and_missing_ids_are_not_invented():
    built = build_context("question", [result("supplied", "Only supplied text", source="known.md")])
    assert "Only supplied text" in built.formatted_context
    assert "invented" not in built.formatted_context
    missing_id = build_context("question", [{"rank": 1, "similarity": 0.5, "text": "No ID", "metadata": {"source": "known.md"}}])
    assert missing_id.evidence == []
    assert missing_id.excluded[0].chunk_id is None
    assert "missing chunk_id" in missing_id.excluded[0].reason


def test_source_is_not_created_when_missing():
    built = build_context("question", [result("known_id", "Text", heading_path="Known")])
    assert built.evidence[0].source == "not available"
    assert "source: not available" in built.formatted_context
