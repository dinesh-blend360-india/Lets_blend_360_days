# Day 06 — Local vector embedding and retrieval

This project turns the Day 05 chunked JSON into local vector embeddings and
ranked similarity-search results. It deliberately stops before RAG: there is no
LLM answer generation, prompt orchestration, access-control layer, or external
vector database.

## Workflow

```text
Day 05 JSON
   ↓ validate + preserve metadata
local BGE-small embeddings (batched, normalized)
   ↓ vectors.npz + metadata.json + manifest.json
query embedding
   ↓ cosine similarity
ranked Top-K chunks with provenance
   ↓ editable labeled queries
Recall@K, MRR, successes, and failures
```

## Why BAAI/bge-small-en-v1.5

`BAAI/bge-small-en-v1.5` is a compact English retrieval model suitable for a
CPU-first learning project. It is expected to produce 384-dimensional vectors,
but the implementation discovers and records the actual dimension instead of
assuming it. The model is loaded through Sentence Transformers and requires no
API key. The first run downloads model files; later local inference can work
without an embedding API or internet access.

For BGE retrieval, the optional query instruction is enabled by default:
`Represent this sentence for searching relevant passages: `. It is added only
to queries, never document passages. Keep this setting constant when comparing
experiments; use `--no-query-instruction` for an explicit alternative run.

## Relationship to Day 05

Day 06 reads the real files in:

```text
ai_engineering/5_document_chunking/outputs/
```

The current Day 05 outputs are:

- `employee_policy_docx_chunked.json`
- `employee_policy_md_chunked.json`
- `employee_policy_pdf_chunked.json`
- `employee_policy_txt_chunked.json`

The loader accepts either a direct list or the Day 05 object format with a
top-level `chunks` list. Older chunks without `chunk_id` receive deterministic
IDs; existing valid IDs are preserved. Day 05 source files are never copied or
modified.

## Folder structure

```text
6_embedding_and_retrival/
├── README.md, SETUP.md, requirements.txt, .env.example
├── src/
│   ├── config.py
│   ├── embeddings/       # validation, BGE provider, index builder
│   ├── retrieval/        # cosine similarity and CLI search
│   └── evaluation/       # Recall@K and MRR evaluation
├── tests/                # no real model download required
├── test_inputs/          # editable retrieval_queries.json
└── outputs/
    ├── embeddings/       # separate index per chunking experiment
    ├── retrieval_results/
    └── reports/
```

## Example commands

Run these from `ai_engineering/6_embedding_and_retrival` after installing the
shared requirements from `ai_engineering/requirements.txt`. The commands below
use the actual Day 05 Markdown output.

```powershell
$day05 = "..\5_document_chunking\outputs\employee_policy_md_chunked.json"
$index = ".\outputs\embeddings\employee_policy_md_structure"

python -m pip install -r ..\requirements.txt
python -m src.embeddings.build_embeddings $day05 --index-dir $index
python -m src.retrieval.search --index-dir $index --query "When is a receipt required?" --top-k 5 --export .\outputs\retrieval_results\receipt.json
python -m src.evaluation.evaluate_retrieval --queries .\test_inputs\retrieval_queries.json --index-dir $index --output .\outputs\reports\employee_policy_md_structure.json
```

Use a separate index directory for the character baseline:

```powershell
$character = "..\5_document_chunking\outputs\employee_policy_md_character_chunked.json"
python -m src.embeddings.build_embeddings $character --index-dir .\outputs\embeddings\employee_policy_md_character
```

The same pattern can be used for all four Day 05 outputs:

```powershell
$day05Files = @(
  "employee_policy_docx_chunked.json",
  "employee_policy_md_chunked.json",
  "employee_policy_pdf_chunked.json",
  "employee_policy_txt_chunked.json"
)
foreach ($file in $day05Files) {
  $name = [IO.Path]::GetFileNameWithoutExtension($file)
  python -m src.embeddings.build_embeddings `
    "..\5_document_chunking\outputs\$file" `
    --index-dir ".\outputs\embeddings\$name"
}
```

Do not mix indexes: model ID, query-instruction setting, vector dimension, and
chunk set are checked before search.

## Stored metadata and scores

`metadata.json` keeps the original text and metadata plus Day 06 fields:
`chunk_id`, `source_hash`, `content_hash`, and `source_is_day05`. Available
`source`, page, heading, chunk index, content type, and overlap fields remain
unchanged. `manifest.json` records the input file hash, model/configuration,
vector dimension, tokenizer limit, normalization, query setting, cache counts,
and every skipped over-limit chunk with a reason.

Vectors are normalized and ranked with cosine similarity. A larger score means
the vectors point in a more similar direction; it is not a probability and is
not proof that a result is correct. Top-K is configurable and defaults to 5.

If a chunk exceeds the loaded tokenizer limit, it is reported and skipped
rather than silently truncated. Re-chunk the source, reduce the Day 05 chunk
size, or intentionally design a documented truncation policy before embedding.

## Evaluation

`test_inputs/retrieval_queries.json` uses source-grounded text phrases so the
evaluator can resolve expected chunk IDs against the actual index. Add explicit
`expected_chunk_ids` when you want stable hand-labeled IDs. Queries with no
matching expected passage are reported separately from ordinary retrieval
failures. Metrics are Recall@1, Recall@3, Recall@5, and MRR.

The implementation and unit-test files are present, but model-based embedding
and retrieval metrics are not claimed until the setup and evaluation commands
have been executed locally. Generated files appear under `outputs/` and are
ignored by Git.

## RAG-readiness checklist

### Document preparation

- [x] Document provenance and source identity are retained.
- [x] Stable chunk IDs are available.
- [x] Source versions or content hashes are recorded.
- [x] Section, page, and content-type metadata are retained where available.
- [x] Chunk quality and missing metadata have been validated.
- [ ] Document freshness and reprocessing requirements are documented.

### Embeddings

- [x] Model ID and configuration are recorded.
- [x] Vector dimensions are validated.
- [x] Token limits are checked.
- [x] Document and query embedding settings are compatible.
- [x] Embedding outputs are reproducible and traceable.
- [x] Unchanged chunks can reuse cached vectors.
- [x] Changed chunks can be re-embedded.

### Retrieval

- [x] Top-K similarity search works.
- [x] Results include source and section metadata.
- [x] Recall@K and MRR are measured against labeled queries.
- [x] Retrieval failure cases are recorded.
- [x] The system rejects incompatible embedding spaces.
- [x] The local storage design can be replaced by a vector database later.

### Production and security preparation

- [ ] Document ownership and access permissions are understood.
- [ ] Future retrieval can filter results by user or document permissions.
- [x] Sensitive text, credentials, and secrets are not logged unnecessarily.
- [ ] Document updates, deletions, and re-indexing have a documented strategy.
- [x] Provenance is sufficient to trace a retrieved chunk to its source.
- [ ] A future answer-generation layer could cite the retrieved source and location.

The checked items describe implementation in this project, not production
readiness. Access control, deployment, a vector database, and answer generation
remain outside scope.

## Known limitations and next improvements

The first provider is English-only BGE-small, local CPU inference may be slow,
and the initial storage is NumPy rather than a production vector database.
Evaluation labels are intentionally small and editable. Future work can add
more labeled queries, compare structure-aware and character indexes, add hybrid
BM25+dense retrieval, add a reranker, and document update/deletion workflows.
