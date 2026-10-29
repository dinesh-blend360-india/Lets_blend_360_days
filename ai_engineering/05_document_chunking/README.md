# Document parsing and chunking

This exercise prepares local PDF, DOCX, TXT, and Markdown files for a later
embedding and retrieval pipeline. The script parses a document, creates chunks,
adds traceable metadata, validates the result, and writes an experiment JSON
file.

## Run it

From this folder:

```powershell
python .\parse-and-chunk.py .\samples\employee_policy_markdown_sample.md `
  --method structure `
  --chunk-size 1000 `
  --overlap 150 `
  --quality-report `
  --output .\outputs\employee_policy_markdown_structure_chunked.json
```

The four sample inputs are:

- `employee_policy_pdf_sample.pdf`
- `employee_policy_docx_sample.docx`
- `employee_policy_text_sample.txt`
- `employee_policy_markdown_sample.md`

If `--output` is omitted, the script creates a method-specific filename such
as `employee_policy_markdown_structure-chunked.json`. Structure-aware and raw
character experiments therefore cannot accidentally share an output file.

## Methods

`structure` is the recommended method for normal policy and handbook content.
It recognizes headings, paragraphs, lists, and Markdown-like tables; carries
heading context into the chunk; preserves PDF page information; and splits
large tables by rows when possible.

`character` is a genuine raw character-window baseline. It does not parse
headings, lists, or tables and is useful for comparing retrieval quality
against the structure-aware experiment. `paragraph`, `sentence`, `word`, and
`recursive` are also available as raw text baselines.

All methods use character counts for now. The script validates that every final
chunk is non-empty, has source metadata, has a unique stable `chunk_id`, and
does not exceed `--chunk-size`.

## Output format

Each result is an object containing:

- `experiment`: method, chunk size, overlap, and source document
- `validation`: checks performed and maximum output size
- `chunks`: text plus metadata
- `quality_report`: optional diagnostics when `--quality-report` is supplied

The chunk metadata includes a deterministic `chunk_id`, source, chunk indexes,
content type, heading path where available, PDF page location where available,
and recorded overlap.

## Manual verification checklist

Run the four sample documents with `--method structure`, inspect the JSON, and
confirm that headings, tables, page metadata, and DOCX table content are
present. Then run the same files with `--method character` and verify that the
output is a raw character baseline with a different filename. A deliberately
long table row should also be tested to confirm that every output chunk remains
within the configured character limit.

## Next section: embeddings and retrieval

Embedding and retrieval are intentionally kept as a separate upcoming step.
The choice should be made after measuring chunk quality and selecting the target
language/domain.

Suggested starting points to evaluate:

- A hosted general-purpose option such as OpenAI `text-embedding-3-small` for
  a cost-effective baseline; compare it with `text-embedding-3-large` when
  recall quality matters more than cost.
- A local multilingual option such as `BAAI/bge-m3` when data must remain
  local or multilingual retrieval is important. Check its licensing and
  hardware requirements before adopting it.

For retrieval, start with dense vector search using cosine similarity and
returning the top 5–10 chunks. Then evaluate a hybrid system combining dense
search with BM25, followed by a reranker such as a cross-encoder when the
candidate set is large. Keep `chunk_id`, source, page, heading path, and the
experiment configuration with every vector so results remain auditable.

Before embedding, use the selected model's tokenizer to measure every chunk and
identify truncation. Compare the structure-aware and character baselines on a
small question set using Recall@k, answer faithfulness, citation accuracy, and
duplicate-token overhead. Tune chunk size and overlap from those results rather
than assuming the current 1,000-character/150-character defaults are optimal.
