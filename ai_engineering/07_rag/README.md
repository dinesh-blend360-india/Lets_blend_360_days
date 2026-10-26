# Day 07 — RAG Phase 5: end-to-end testing

Phase 5 tests the complete retrieval → context → local LLM → citation
validation pipeline. It preserves the Phase 1–4 components and does not change
the Day 06 index, retrieval settings, or embeddings.

## What was inspected and reused

The workspace contains:

- Day 05 chunks under `../05_document_chunking/outputs/`
- Day 06 retrieval code under `../06_embedding_and_retrieval/src/retrieval/`
- Day 06 configuration under `../06_embedding_and_retrieval/src/config.py`
- Day 06 BGE provider under `../06_embedding_and_retrieval/src/embeddings/bge_provider.py`
- Day 06 query examples under `../06_embedding_and_retrieval/test_inputs/`
- Real Day 06 indexes under `../06_embedding_and_retrieval/outputs/embeddings/`

The available real indexes are:

```text
employee_policy_md_structure
employee_policy_md_no_instruction
```

Both manifests identify `BAAI/bge-small-en-v1.5`, 384-dimensional vectors, and
11 indexed chunks. The structure index has query instruction enabled; the
no-instruction index has it disabled. The adapter does not regenerate either
index.

## Adapter behavior

`rag/day06_adapter.py` delegates to Day 06's `src.retrieval.search.search_index`.
That preserves the existing Day 06 behavior and its compatibility checks for:

- Model ID
- Vector dimension
- Query-instruction setting
- Cosine similarity ranking
- Top-K behavior

Returned results preserve the original `chunk_id`, text, similarity score, and
metadata such as source, page, heading path, content type, and chunk indexes.

The selected index is configurable. Resolution order is:

1. `--index-dir`
2. `DAY06_INDEX_DIR`
3. The repository-relative structure index

No machine-specific absolute path is hardcoded in configuration.

## Context construction

`rag/context_builder.py` accepts a question and the result list returned by the
Day 06 adapter. It returns a `ContextBuildResult` containing:

- `formatted_context`: human-readable, `[EVIDENCE]`-delimited blocks
- `evidence`: structured included records with IDs, text, retrieval data, and
  copied original metadata
- `excluded`: supplied records excluded from the context, with a reason and
  required/remaining character counts
- `used_context_chars` and `max_context_chars`

Evidence blocks are atomic. If a complete block does not fit the configured
budget, it is excluded rather than silently truncating its text. Missing IDs,
empty text, and missing optional metadata are handled explicitly. Missing
source, section, or page values are rendered as `not available`; no source IDs
or chunk IDs are invented.

Retrieved text is untrusted evidence. The builder formats it as data and does
not execute, follow, summarize, or reinterpret instructions that may appear in
the retrieved text.

Example call:

```python
from rag.context_builder import build_context
from rag.day06_adapter import search

results = search("When is a receipt required?", top_k=5)
context = build_context("When is a receipt required?", results, max_context_chars=6000)
print(context.formatted_context)
```

The structured result keeps an explicit mapping from each formatted block to
its original `chunk_id` and metadata.

## Grounded answer generation

`rag/answer_generator.py` is a separate component. It accepts:

- The user question
- The formatted Phase 2 evidence context
- The explicit allowed evidence ID list

It calls Ollama using `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TEMPERATURE`,
`OLLAMA_NUM_PREDICT`, and `OLLAMA_TIMEOUT_SECONDS`. The default model is
`llama3.2:3b`; this is configurable and is not downloaded automatically.

The prompt labels retrieved text as untrusted evidence. The generator never
uses an empty evidence set to call the model: it returns the explicit
insufficient-evidence response immediately. Supported model responses must cite
at least one allowed ID. Unknown citations, missing citations, malformed JSON,
and contradictory response fields raise `GenerationError` rather than being
silently repaired.

The response contract is:

```json
{
  "answer": "A concise evidence-grounded answer.",
  "insufficient_evidence": false,
  "citations": ["chunk_abc123"]
}
```

If Ollama is unavailable, the CLI reports the model, host, and setup action
instead of claiming that generation succeeded.

Run it after constructing context and saving that context to a UTF-8 file:

```powershell
python -m rag.answer_generator `
  --question "When is a receipt required?" `
  --context-file .\outputs\receipt_context.txt `
  --allowed-ids chunk_5762afc8dde264e56dd
```

The generator does not construct context itself and does not perform retrieval;
those remain separate functions.

## Citation validation and orchestration

`rag/citation_validator.py` maps only model-cited IDs that belong to the actual
Phase 2 evidence records. Final `citations` and `sources` are built from the
original evidence metadata, never from model-supplied source descriptions.
Unknown, malformed, or missing citations for a supported answer raise a
controlled `CitationValidationError`. Duplicate IDs are deduplicated.

`rag/pipeline.py` exposes the single callable Phase 4 entry point:

```python
from rag.pipeline import run_rag

response = run_rag(
    "When is a receipt required?",
    top_k=5,
    max_context_chars=6000,
    include_debug=True,
)
```

The command-line equivalent is:

```powershell
python -m rag.pipeline `
  --question "When is a receipt required?" `
  --top-k 5 `
  --max-context-chars 6000 `
  --debug
```

With debug enabled, only retrieval counts, IDs, ranks, and similarity scores
are exposed; prompts and document text are not added to debug output.

## Phase 5 test cases and results

The editable cases are in:

```text
test_inputs/rag_test_cases.json
```

They cover direct facts, numeric thresholds, exceptions, travel, a table lookup,
unsupported/weak/incomplete evidence, empty retrieval, unknown citations,
generation failures, and instruction injection. Known IDs were checked against
the real Day 06 structure index metadata. The mocked runner is:

```powershell
python -m rag.phase5_runner
```

It writes readable results to:

```text
outputs/phase5_rag_test_results.json
```

Each result records the query, answer or error, insufficiency flag, citations,
retrieval IDs/ranks/scores, and pass/fail status. The default unit suite does
not download a model. Optional real-index/Ollama testing is enabled separately:

```powershell
$env:RUN_RAG_INTEGRATION = "1"
python -m pytest .\tests -m integration -q
```

Do not claim an integration pass unless Ollama, the configured model, and the
real Day 06 index are available and the command succeeds.

## Phase 6 status

The Phase 5 test command was attempted, but execution was blocked before test
collection because no usable `python`, `py`, or `ollama` command is available in
the current environment. No Phase 5 result JSON was present to analyze. The
failure analysis is recorded in [outputs/failure_analysis.md](outputs/failure_analysis.md).

No prompt, retrieval setting, or implementation change was made speculatively.
After Python is repaired, run the commands in `SETUP.md`, inspect the generated
Phase 5 results, and then classify any actual failure through retrieval,
context, generation, and citation stages.

Example based on the real Day 06 structure index result for the receipt query:

```text
[EVIDENCE]
chunk_id: chunk_5762afc8dde264e56dd
source: Day5_document_Chunking_Samples\employee_policy_markdown_sample.md
section: Employee Expense and Travel Policy > 2. Expense Reimbursement Rules > 2.1 Submission deadline and required context
page: not available
rank: 1
similarity: 0.8019

Text:
Section: 2.1 Submission deadline and required context

Employees must submit expense claims within 30 calendar days of the purchase date. Every claim must include the purchase date, amount, business purpose, and the name of the project or customer. These details must remain together so a reviewer can understand what the expense was for.

A readable receipt is required for each expense of 500 currency units or more. If a receipt is unavailable, the employee must attach a written explanation and obtain manager approval before Finance reviews the claim. The explanation does not automatically guarantee reimbursement.
[/EVIDENCE]
```

The evidence ID, rank, similarity, and text in this example come from the real
Day 06 exported retrieval result at
`../06_embedding_and_retrieval/outputs/retrieval_results/receipt.json`.

## Run it

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements.txt

python -m rag.day06_adapter `
  --query "When is a receipt required?" `
  --top-k 5
```

To select the no-instruction Day 06 index explicitly:

```powershell
python -m rag.day06_adapter `
  --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_no_instruction `
  --query "When is a receipt required?" `
  --top-k 5
```

To export results:

```powershell
python -m rag.day06_adapter `
  --query "When is a receipt required?" `
  --export .\outputs\receipt_search.json
```

The adapter creates the export directory when needed. It does not create new
embeddings.

## Tests

```powershell
python -m pytest .\tests -q
```

The tests mock the Day 06 retrieval module and therefore do not download the
BGE model. A real-index smoke test requires a working Python environment and
the existing Day 06 model/runtime dependencies.

## Phase 5 limitations

- No UI selector
- No access-control filtering
- No new vector database
- No automatic index regeneration

Those belong to later phases. If the selected Day 06 index is missing or its
manifest is incompatible with the query configuration, the adapter reports the
error rather than fabricating results.
