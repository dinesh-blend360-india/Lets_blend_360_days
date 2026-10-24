# Day 08 — RAG Evaluation Framework

This project evaluates the existing Day 07 RAG pipeline without modifying it. It records what evidence exists, what retrieval returned, what context reached the model, what answer was generated, and whether citations map back to supplied evidence.

## What is evaluated

```text
versioned test cases
  → Day 07 retrieval
  → Day 07 context builder
  → Day 07 local Ollama generator
  → Day 07 citation validator
  → Day 08 evidence/answer checks
  → failure classification and reports
```

The adapter imports these existing Day 07 interfaces read-only:

- `rag.day06_adapter.search` and `inspect_index`
- `rag.context_builder.build_context`
- `rag.answer_generator.generate_answer`
- `rag.citation_validator.validate_citations`

The selected Day 06 index remains configurable through `DAY06_INDEX_DIR`. Day 08 never regenerates vectors or changes Day 07 behavior.

## Corpus audit

The configured structure-aware index contains 11 chunks from `Day5_document_Chunking_Samples\employee_policy_markdown_sample.md`. Its manifest specifies `BAAI/bge-small-en-v1.5`, 384-dimensional normalized vectors, and the BGE query instruction.

The source covers expense reimbursement and business travel. It does **not** contain annual leave, vacation leave, a leave approval threshold, international-trip business-unit approval, parental leave, or sick leave. Those seven evaluation cases are labelled `MISSING_FROM_CORPUS` and must be reported as `BLOCKED_MISSING_SOURCE`, even when the model correctly abstains.

The receipt-threshold case is supported. `chunk_5762afc8dde2640e56dd` states that a readable receipt is required for each expense of **500 currency units or more**. This ID was verified against the real Day 06 `metadata.json`.

## Eight common cases

| Case ID | Purpose | Corpus status |
|---|---|---|
| `annual_leave_direct` | Direct annual-leave fact | Missing |
| `vacation_leave_paraphrase` | Paraphrased annual leave | Missing |
| `five_consecutive_days_approval` | Conditional leave rule | Missing |
| `international_trip_approvals` | Multi-part approval | Missing |
| `receipt_numeric_threshold` | Exact monetary threshold | Supported |
| `parental_leave_unsupported` | Unsupported policy | Missing |
| `annual_vs_parental_leave` | Mixed comparison requested by assignment | Both parts missing |
| `sick_leave_exact_terminology` | Exact source terminology | Missing |

Cases and evidence labels live in [test_inputs/day08_common_cases.json](test_inputs/day08_common_cases.json). Add future suites as separate JSON files; expected evidence is kept separate from answer wording.

## Run it

From this folder, after following [SETUP.md](SETUP.md):

```powershell
python -m pip install -r requirements.txt
python -m pytest -m "not integration" -q
python -m src.evaluator
python -m src.evaluator --case-id receipt_numeric_threshold
```

Day 08's `requirements.txt` delegates to the common `ai_engineering/requirements.txt`, keeping dependencies in one shared file.

The default test suite is mocked and does not download an embedding or LLM model. To deliberately run the optional real integration test:

```powershell
$env:RUN_DAY08_INTEGRATION = "1"
python -m pytest tests/test_integration.py -m integration -v
```

## Results and metrics

Each evaluation creates `outputs/runs/<UTC-run-id>/` with:

- `results.json`: complete captured records, including ranked chunks and exact context.
- `results.csv`: concise comparison table.
- `summary.md`: status and metric summary.
- `run_manifest.json`: paths, Top-K, context budget, evidence-label audit, index details, and execution time.

`outputs/summaries/latest_summary.md` points to the newest outcome in readable form. `outputs/failure_analysis/failure_analysis.md` lists the evidence supporting each non-pass diagnosis. Existing run directories are never overwritten.

Retrieval Recall@1/3/5 and reciprocal rank are calculated only when verified expected chunk IDs exist. In this corpus that means the receipt case. Cases without source labels receive no invented retrieval score. Deterministic answer checks verify required/forbidden phrases and abstention behavior, but semantic grounding remains `NEEDS_MANUAL_REVIEW`; keyword checks alone cannot prove answer quality.

Status meanings:

- `PASS`: all automated requirements passed and no manual review remains.
- `FAIL`: evidence existed but retrieval, context, generation, or citations failed.
- `BLOCKED_MISSING_SOURCE`: the required fact is absent from the corpus.
- `SKIPPED_RUNTIME_UNAVAILABLE`: Python dependencies, index access, Ollama, or its configured model prevented execution.
- `NEEDS_MANUAL_REVIEW`: deterministic checks passed, but claim-level semantic support still needs review.

Failure stages are `CORPUS_COVERAGE`, `RETRIEVAL`, `CONTEXT_CONSTRUCTION`, `GENERATION_GROUNDING`, `CITATION_MAPPING`, and `RUNTIME_OR_CONFIGURATION`. Diagnose in that order: first verify the fact exists, then inspect ranks, exact context, raw answer, and citation mapping.

## Limitations

- Seven assignment questions cannot evaluate retrieval success until matching HR policy sources are deliberately added and indexed in a future data-preparation exercise.
- Day 07 does not expose a raw pre-parse Ollama response, so Day 08 captures the validated generated contract or its raised error, not malformed raw model text.
- Answer checks are intentionally conservative and require manual semantic review.
- Real runs require the existing BGE dependencies and a locally installed Ollama model; no model is downloaded automatically.

