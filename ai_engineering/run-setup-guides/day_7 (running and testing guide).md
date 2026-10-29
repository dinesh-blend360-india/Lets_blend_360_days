# Day 07 — RAG running and testing guide

**AI Engineering Program | Day 07: retrieval, context, grounded generation, citation validation, and testing**

This guide covers the complete Day 07 workflow in:

```text
ai_engineering/07_rag/
```

Day 07 reuses the real Day 06 retrieval adapter and structure-aware index. It
does not modify Day 05 or Day 06 files.

## 1. Day 07 scope

The implemented pipeline is:

```text
Question
  → Day 06 retrieval
  → bounded evidence context
  → local Ollama model
  → deterministic citation validation
  → final grounded response
```

The project includes:

- Phase 1: Day 06 retrieval adapter
- Phase 2: context construction
- Phase 3: local Ollama answer generation
- Phase 4: citation validation and orchestration
- Phase 5: mocked and optional end-to-end tests
- Phase 6: failure-analysis documentation

The project does not include a UI, agents, MCP, another vector database, or an
unrelated answer-generation pipeline.

## 2. Open the project folder

Open PowerShell and move to the Day 07 project:

```powershell
cd C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\07_rag
```

The shared workspace layout is:

```text
ai_engineering/
├── 05_document_chunking/
├── 06_embedding_and_retrieval/
├── 07_rag/
│   ├── rag/
│   ├── tests/
│   ├── test_inputs/
│   ├── outputs/
│   ├── README.md
│   ├── SETUP.md
│   └── requirements.txt
└── requirements.txt
```

## 3. Simple setup

Check Python:

```powershell
python --version
```

Create an isolated Day 07 environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe --version
```

Install the shared workspace dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Alternatively, install the Day 07 dependency reference:

```powershell
python -m pip install -r .\requirements.txt
```

The first local embedding or Ollama run may require internet access depending on
which model files are already cached. Day 07 does not automatically download a
large Ollama model.

## 4. Configure Day 06 index selection

The default Day 06 index is the structure-aware Markdown index:

```powershell
$env:DAY06_INDEX_DIR = "..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure"
```

The alternative existing index is:

```text
..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_no_instruction
```

You can also pass `--index-dir` directly to the commands. Do not mix indexes
with different model or query-instruction settings.

## 5. Configure Ollama for Phase 3 and Phase 4

Set the local Ollama connection and model:

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "llama3.2:3b"
$env:OLLAMA_TEMPERATURE = "0.0"
$env:OLLAMA_NUM_PREDICT = "256"
$env:OLLAMA_TIMEOUT_SECONDS = "120"
```

Check whether Ollama is installed and running:

```powershell
ollama list
```

If the configured model is not installed, pull it only after confirming its
size is appropriate for the machine:

```powershell
ollama pull llama3.2:3b
```

If Ollama or the model is unavailable, Day 07 reports a setup error rather than
pretending that answer generation succeeded.

## 6. Run the existing unit tests

Run the complete default suite from the Day 07 folder:

```powershell
python -m pytest .\tests -q
```

These tests use mocked retrieval, vectors, and Ollama responses. They do not
require a model download.

Run only the Phase 5 case tests:

```powershell
python -m pytest .\tests\test_phase5_cases.py -q
```

Run the citation and orchestration tests:

```powershell
python -m pytest .\tests\test_citation_and_pipeline.py -q
```

Run the generator tests:

```powershell
python -m pytest .\tests\test_answer_generator.py -q
```

## 7. Phase 1 — Test Day 06 retrieval adapter

Run a retrieval query using the existing structure-aware index:

```powershell
python -m rag.day06_adapter `
  --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure `
  --query "When is a receipt required?" `
  --top-k 5 `
  --export .\outputs\receipt_retrieval.json
```

The result preserves:

- `chunk_id`
- Original chunk text
- Similarity score
- Rank
- Source path
- Heading path
- Page information when available

## 8. Phase 2 — Build evidence context

The context builder accepts retrieval results and returns formatted evidence plus
structured evidence records. It does not retrieve or generate answers.

Example using the adapter from PowerShell:

```powershell
python -c "from rag.day06_adapter import search; from rag.context_builder import build_context; r=search('When is a receipt required?', top_k=5); c=build_context('When is a receipt required?', r, max_context_chars=6000); print(c.formatted_context); print('Included IDs:', [e.chunk_id for e in c.evidence]); print('Excluded:', [e.as_dict() for e in c.excluded])"
```

Evidence blocks are atomic. If a block does not fit the configured context
budget, it is excluded with a reason instead of being silently truncated.

## 9. Phase 3 — Test local grounded generation

First save the Phase 2 `formatted_context` to a UTF-8 file, then pass the exact
IDs from the evidence records:

```powershell
python -m rag.answer_generator `
  --question "When is a receipt required?" `
  --context-file .\outputs\receipt_context.txt `
  --allowed-ids chunk_5762afc8dde264e56dd
```

The generator returns JSON with:

```json
{
  "answer": "...",
  "insufficient_evidence": false,
  "citations": ["chunk_5762afc8dde264e56dd"]
}
```

For empty evidence, it returns the explicit insufficient-evidence response. It
rejects malformed output and citations that are not present in the allowed
evidence context.

## 10. Phase 4 — Run the complete RAG pipeline

The orchestration function runs retrieval, context construction, generation, and
citation validation:

```powershell
python -m rag.pipeline `
  --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure `
  --question "When is a receipt required?" `
  --top-k 5 `
  --max-context-chars 6000 `
  --debug
```

The final response contains:

- `answer`
- `insufficient_evidence`
- Validated citation objects
- `sources`
- Optional debug retrieval count, IDs, ranks, and scores

Debug output does not include prompts or copied document text.

## 11. Phase 5 — Run all mocked cases and save results

The 13 editable cases are in:

```text
test_inputs/rag_test_cases.json
```

Run the deterministic mocked case runner:

```powershell
python -m rag.phase5_runner
```

Read the generated results:

```powershell
Get-Content .\outputs\phase5_rag_test_results.json
```

The result file records:

- Query ID and question
- Expected outcome
- Answer or error
- Insufficiency flag
- Citation IDs
- Retrieval IDs, ranks, and scores
- Pass/fail status

The cases cover direct factual questions, thresholds, exceptions, travel,
workflow, table lookup, unsupported questions, unknown IDs, empty retrieval,
weak evidence, incomplete evidence, generation failure, and prompt injection.

## 12. Optional real end-to-end integration test

This test requires:

- A working Python environment
- The real Day 06 structure-aware index
- Ollama running locally
- The configured Ollama model installed

Enable it explicitly:

```powershell
$env:RUN_RAG_INTEGRATION = "1"
python -m pytest .\tests -m integration -q
```

Do not claim integration success if this command is skipped or fails. The
default unit suite does not require Ollama.

## 13. Phase 6 — Review failure analysis

If tests fail, diagnose in this order:

1. Retrieval: was the expected chunk present and retrieved?
2. Context: was it included without losing necessary text or metadata?
3. Generation: did the model use only the supplied evidence and return valid JSON?
4. Citation: do cited IDs map to the supplied evidence metadata?

Read the current analysis:

```powershell
Get-Content .\outputs\failure_analysis.md
```

After a real Phase 5 run, update this file with retrieved IDs, ranks, scores,
context references, primary failure stage, evidence, and a justified fix. Do not
rewrite prompts or retrieval settings merely to make a case pass.

## 14. Important output locations

```text
07_rag/outputs/
├── phase5_rag_test_results.json       # mocked case results
├── failure_analysis.md                # Phase 6 diagnosis
└── *.json / *.txt                     # optional retrieval/context exports
```

Day 06 source indexes remain under:

```text
06_embedding_and_retrieval/outputs/embeddings/
```

Do not overwrite or regenerate them just to run Day 07 tests.

## 15. Troubleshooting

### Python is not recognized

Install Python or repair the environment, then retry:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r ..\requirements.txt
```

### Ollama is unavailable

Check:

```powershell
ollama list
```

Start Ollama, confirm the model name in `$env:OLLAMA_MODEL`, and retry. Do not
replace the failure with a fabricated answer.

### Index is missing

Confirm the Day 06 structure index exists:

```powershell
Get-ChildItem ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure
```

The directory should contain `vectors.npz`, `metadata.json`, and `manifest.json`.

### Citation validation fails

Check that every allowed ID appears in the evidence context and that every model
citation is an actual supplied chunk ID. Do not add a citation manually just to
make validation pass.

## 16. Completed versus pending

Completed in the implementation:

- Day 06 retrieval reuse
- Bounded evidence context construction
- Configurable Ollama generation
- Citation validation
- Single-callable RAG orchestration
- Mocked Phase 5 test cases
- Optional integration-test definition
- Failure-analysis document

Pending until the environment is repaired and commands are executed:

- Actual default pytest results
- Actual mocked Phase 5 result JSON
- Actual Ollama generation result
- Actual real-index end-to-end integration result
