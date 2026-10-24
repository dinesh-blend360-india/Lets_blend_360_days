# Day 08 setup and running guide (Windows PowerShell)

## 1. Open the project folder

```powershell
Set-Location C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\8_rag_evaluation
```

## 2. Activate the existing environment

If the repository virtual environment already works:

```powershell
& ..\..\venv\Scripts\Activate.ps1
python --version
```

If that environment does not exist, create a local one with an installed Python 3.10+ interpreter:

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1
```

## 3. Install the common dependencies

Day 08 inherits the common `ai_engineering/requirements.txt` through its local requirements file:

```powershell
python -m pip install -r requirements.txt
```

You can also install the common file directly from this folder; both commands install the same dependency list:

```powershell
python -m pip install -r ..\requirements.txt
```

The common requirements include pytest, Ollama's Python package, NumPy, and Sentence Transformers. Installing them does not download an Ollama model.

## 4. Configure paths and model

```powershell
Copy-Item .env.example .env
```

Environment files are not loaded automatically by Day 08. Either keep the defaults or set overrides in the shell:

```powershell
$env:DAY07_PROJECT_DIR = "..\7_rag"
$env:DAY06_INDEX_DIR = "..\6_embedding_and_retrival\outputs\embeddings\employee_policy_md_structure"
$env:OLLAMA_MODEL = "llama3.2:3b"
```

Relative paths are resolved from `8_rag_evaluation`.

## 5. Verify prerequisites

Check the real index files:

```powershell
Get-ChildItem $env:DAY06_INDEX_DIR
Get-Content "$env:DAY06_INDEX_DIR\manifest.json"
```

Check Ollama and installed models:

```powershell
ollama --version
ollama list
```

If the configured model is absent, install it manually only if you want a real integration run:

```powershell
ollama pull $env:OLLAMA_MODEL
```

## 6. Run mocked unit tests

```powershell
python -m pytest -m "not integration" -q
```

These tests cover dataset validation, duplicate IDs, evidence and citation checks, Recall@K/MRR, failure classification, mocked runtime handling, and historical report preservation.

## 7. Run evaluations

All eight cases against the real Day 07 stages:

```powershell
python -m src.evaluator
```

One case:

```powershell
python -m src.evaluator --case-id receipt_numeric_threshold
```

Inspect without writing a historical run:

```powershell
python -m src.evaluator --case-id receipt_numeric_threshold --no-write
```

Optional pytest integration test:

```powershell
$env:RUN_DAY08_INTEGRATION = "1"
python -m pytest tests\test_integration.py -m integration -v
```

## 8. Find reports

```powershell
Get-ChildItem outputs\runs
Get-Content outputs\summaries\latest_summary.md
Get-Content outputs\failure_analysis\failure_analysis.md
```

Every normal evaluator invocation creates a unique UTC run directory containing JSON, CSV, Markdown summary, and a manifest.

## Troubleshooting

- **`python` or `py` is not recognized:** install Python 3.10+ and recreate the environment. A copied virtual environment may point to a Python executable that no longer exists.
- **Missing model/package:** install `..\requirements.txt`, start Ollama, and verify the exact `OLLAMA_MODEL` appears in `ollama list`.
- **Missing index:** verify the three Day 06 files `manifest.json`, `metadata.json`, and `vectors.npz`; do not regenerate them merely to run Day 08.
- **Expected evidence not found:** check the corpus status first. Seven current cases are intentionally blocked because their HR policies do not exist in the index.
- **Invalid citation:** compare `generated_citation_ids` with `context.evidence[].chunk_id` in `results.json`. Day 07 rejects unknown IDs.
- **Context omission:** compare `retrieved_ids` with `context_ids`; inspect `context.excluded` for context-budget reasons.
- **Runtime error:** inspect the structured `errors` array and `primary_failure_stage` in `results.json`.

