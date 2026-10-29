# Day 07 Phase 5 setup

Open PowerShell in:

```text
C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\07_rag
```

Create an isolated environment if needed and install the shared workspace
dependencies:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Day 07 reuses the Day 06 Sentence Transformers, NumPy, and pytest dependencies.
The first real search may need the locally cached BGE model; no new model or
embedding index is created by this phase.

## Select a Day 06 index

The default is the repository-relative structure-aware index:

```powershell
$env:DAY06_INDEX_DIR = "..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure"
```

Or pass the path directly to the command. The existing alternative index is:

```text
..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_no_instruction
```

Keep the query-instruction configuration consistent with the selected manifest.
Day 06 enforces this during search.

## Configure Ollama

The generator uses the local Ollama service and does not download a model
automatically. Set the model and host before running generation:

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "llama3.2:3b"
$env:OLLAMA_TEMPERATURE = "0.0"
$env:OLLAMA_NUM_PREDICT = "256"
$env:OLLAMA_TIMEOUT_SECONDS = "120"
```

If Ollama is installed, check available models:

```powershell
ollama list
```

If the configured model is not listed, install it explicitly and only after
confirming that its size is acceptable for the machine:

```powershell
ollama pull llama3.2:3b
```

If Ollama or the model is unavailable, the generator returns an actionable
setup error and does not pretend that an answer was generated.

## Run a real retrieval smoke test

```powershell
python -m rag.day06_adapter `
  --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure `
  --query "When is a receipt required?" `
  --top-k 5 `
  --export .\outputs\receipt_search.json
```

The results should contain ranked chunks with the original Day 06 IDs, text,
similarity, and metadata. If the index is missing, the command reports the
missing input; it does not regenerate or fabricate an index.

## Build bounded evidence context

Context construction accepts the result list returned by retrieval. It does
not run retrieval itself and does not generate an answer:

```powershell
python -c "from rag.day06_adapter import search; from rag.context_builder import build_context; r=search('When is a receipt required?', top_k=5); c=build_context('When is a receipt required?', r, max_context_chars=6000); print(c.formatted_context); print('Included IDs:', [e.chunk_id for e in c.evidence]); print('Excluded:', [e.as_dict() for e in c.excluded])"
```

The builder includes complete evidence blocks only. When a block would exceed
the budget, it is excluded with an explicit reason; it is not silently cut.
The returned object exposes both formatted context and structured evidence
records.

## Generate a grounded answer

First save the Phase 2 `formatted_context` to a UTF-8 text file and pass the
same evidence IDs that appear in that context. For example:

```powershell
python -m rag.answer_generator `
  --question "When is a receipt required?" `
  --context-file .\outputs\receipt_context.txt `
  --allowed-ids chunk_5762afc8dde2640e56dd
```

The generator validates that supported answers cite only the supplied IDs. It
returns an explicit insufficient-evidence response when context or allowed IDs
are empty, and rejects malformed model output or invented citations.

## Run mocked adapter tests

```powershell
python -m pytest .\tests -q
```

These tests do not download a model. A real-index search is a separate smoke
test because it depends on the existing Day 06 runtime and model cache. Phase 2
context-builder tests use supplied mocked retrieval results and cover IDs,
metadata, empty results, budget exclusions, and source-identifier safety. Phase
3 generator tests mock Ollama responses and cover supported, unsupported,
partial, hostile, malformed, and unavailable-model cases.

## Run the complete Phase 4 pipeline

The orchestration entry point runs Day 06 retrieval, Phase 2 context building,
Phase 3 Ollama generation, and deterministic citation validation:

```powershell
python -m rag.pipeline `
  --question "When is a receipt required?" `
  --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure `
  --top-k 5 `
  --max-context-chars 6000 `
  --debug
```

The final response contains `answer`, `insufficient_evidence`, validated
`citations`, `sources`, and optional debug retrieval information. If there is no
evidence, the pipeline abstains without calling Ollama. If citation validation
fails, it raises a controlled validation error instead of fabricating metadata.

## Run Phase 5 mocked end-to-end tests

Run the normal unit suite; it does not download a model:

```powershell
python -m pytest .\tests -q
python -m rag.phase5_runner
Get-Content .\outputs\phase5_rag_test_results.json
```

The case definitions are in `test_inputs/rag_test_cases.json`. The runner uses
mocked retrieval and generation so failures are deterministic and do not alter
the Day 06 index.

## Run optional real integration testing

Only run this when Ollama is installed, the configured model is available, and
the Day 06 structure index exists:

```powershell
$env:RUN_RAG_INTEGRATION = "1"
python -m pytest .\tests -m integration -q
```

This test performs a real retrieval and local-model generation for the receipt
question. If prerequisites are unavailable, keep it skipped and report that
limitation rather than fabricating an end-to-end result.
