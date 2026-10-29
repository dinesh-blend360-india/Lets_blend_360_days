# AI Engineering — Setup and Run Guide (Days 01–16)

One guide to get this folder running from a clean machine, then run every day's
exercise from Day 01 to Day 16.

Everything here runs **locally**. The models are served by [Ollama](https://ollama.com)
on your own machine; the embedding model runs on CPU through Sentence Transformers.
No API keys are required for any day.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11 or newer | `python --version` |
| Ollama | current | Needed only for the days that call a model (01, 02, 03, 10, 11, 12, 15, 16) |
| Disk space | ~3 GB | PyTorch + Sentence Transformers + the BGE model + Ollama models |
| Internet | first run only | To install packages and download models; after that everything is local |

Install the two Ollama models used by these exercises:

```powershell
ollama pull llama3.2:3b
ollama pull qwen3:4b
```

Confirm Ollama is serving:

```powershell
ollama list
```

> **Pick `llama3.2:3b` when you just want a day to finish.** `qwen3:4b` is a
> reasoning model and can take several minutes per agent loop on CPU. Days 11, 12
> and 15 run a multi-step loop, so a slow model makes them look like they hung.

---

## 2. One-time setup

All commands below assume **PowerShell** on Windows and the repository root:

```text
C:\workspace\IDC-on-boarding-training\Lets_blend_360_days
```

### 2.1 Create the shared virtual environment

There is **one shared `venv` at the repository root** for all sixteen days.
Create it once:

```powershell
Set-Location C:\workspace\IDC-on-boarding-training\Lets_blend_360_days
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\ai_engineering\requirements.txt
```

If PowerShell blocks `Activate.ps1`, skip activation and call the interpreter
directly instead — every command in this guide works that way too:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

`ai_engineering\requirements.txt` is the **canonical dependency list for all
sixteen days**, including the Day 14 `mcp` package. The per-day
`requirements.txt` files (Days 06, 07, 08, 14) are minimal subsets, useful only
if you want to run one day in isolation.

### 2.2 Configure `.env`

Create `ai_engineering\.env` (it is git-ignored — never commit it):

```ini
OLLAMA_MODEL="qwen3:4b"
OLLAMA_HOST="http://localhost:11434"

# Day 6 — local BGE embeddings
EMBEDDING_MODEL_ID=BAAI/bge-small-en-v1.5
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true
EMBEDDING_USE_QUERY_INSTRUCTION=true

# Day 7 / Day 8 — relative to 07_rag and 08_rag_evaluation
DAY06_INDEX_DIR=..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure
```

### 2.3 Verify the setup

From `ai_engineering`, this should report passes for every day:

```powershell
Set-Location .\ai_engineering
$py = "..\venv\Scripts\python.exe"
foreach ($d in @("03_structured_output","04_enhanced_dev_codex","06_embedding_and_retrieval",
                 "07_rag","08_rag_evaluation","09_fine_tuning","10_tool_calling","11_agents",
                 "12_reliable_agentic_workflows","13_agentic_engineering","14_mcp","15_evaluations",
                 "16_observability")) {
  Push-Location $d
  Write-Host "== $d" -ForegroundColor Cyan
  & "..\$py" -m pytest -q --no-header
  Pop-Location
}
```

Expected: **299 passed, 3 skipped** across the thirteen suites. The three skips are
integration tests that need a live model and are skipped by design.

### 2.4 Optional: the three live integration tests

Each is gated behind its own opt-in environment variable, so a normal `pytest`
run never touches a model. Run them once you have Ollama up and, for Days 07 and
08, the Day 06 index built ([§4.6](#46-day-06--embedding-and-retrieval)):

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"

Set-Location .\07_rag
$env:RUN_RAG_INTEGRATION = "1"
& $py -m pytest tests/test_phase5_integration.py -m integration -q

Set-Location ..\08_rag_evaluation
$env:RUN_DAY08_INTEGRATION = "1"
& $py -m pytest tests/test_integration.py -m integration -q

Set-Location ..\10_tool_calling
$env:RUN_DAY10_INTEGRATION = "1"
$env:KNOWLEDGE_BACKEND = "mock"
& $py -m pytest tests/test_live_integration.py -m integration -q
```

Each takes roughly 10–40 seconds. Without the matching variable the test reports
`skipped`, not a failure — if you see a skip where you expected a run, the
variable is the first thing to check.

---

## 3. How the days depend on each other

Most days are standalone, but two chains matter. Run them in order the first time.

```text
05_document_chunking  ──►  06_embedding_and_retrieval  ──►  07_rag  ──►  08_rag_evaluation
   (chunk JSON)              (vector index)                 (answers)     (scores the answers)

10_tool_calling  ──►  11_agents        (agent loop over Day 10 tools)
                 ──►  14_mcp          (serves Day 10 lookup over MCP)
                 ──►  15_evaluations  (evaluates the Day 10 assistant)
```

Day 06's index is **git-ignored**, so a fresh clone has no index. Days 07 and 08
cannot run live until you build it — see [§4.6](#46-day-06--embedding-and-retrieval).

Everything else (01, 02, 03, 04, 09, 12, 13) is independent.

---

## 4. Running each day

Unless noted, `Set-Location` into the day's folder first and use the shared
interpreter `..\venv\Scripts\python.exe` (written `$py` below).

> **The fastest way to see Days 01–16 at once** is the unified Streamlit hub in
> [§5](#5-the-unified-hub). The per-day commands here are the standalone path and
> the one to use when something in the hub misbehaves.

### 4.1 Day 01 — Simple GenAI

A minimal Streamlit chat box over a local Ollama model.

```powershell
Set-Location .\ai_engineering
streamlit run .\01_simple_genAI\app.py
```

Needs Ollama running. Sample outputs are in `01_simple_genAI/results.txt`.

### 4.2 Day 02 — Context levels

Compares a bare prompt against layered instructions and full context, so you can
see what context actually buys.

```powershell
streamlit run .\02_with_context_level\context_experiments.py
```

`mentor_given.py` is the reference implementation from the session. Recorded
results: `02_with_context_level/day02_prompt_context_actual_results.md`.

### 4.3 Day 03 — Structured output and validation

Pydantic-validated model output with a bounded retry loop.

```powershell
Set-Location .\03_structured_output
streamlit run .\structured_validation.py
& $py -m pytest -q          # 13 tests, no model needed
```

`reliability.py` holds the retry/validation core; the tests exercise it with a
fake client, so they pass without Ollama.

### 4.4 Day 04 — Task Management API

A FastAPI + SQLite CRUD service. The batch file handles the venv, dependencies
and the server in one step:

```powershell
Set-Location .\04_enhanced_dev_codex
.\run.bat --check      # verify dependencies only
.\run.bat              # start on http://127.0.0.1:8000/docs
.\run.bat 8080         # or choose a port
```

Equivalent manual commands:

```powershell
& $py -m uvicorn task_api.main:app --app-dir . --reload
& $py -m pytest -q     # 64 tests
```

The SQLite file is created at `04_enhanced_dev_codex/data/tasks.db` on first
start and is git-ignored. Override with `TASK_DB_PATH`.

### 4.5 Day 05 — Document chunking

Parses PDF/DOCX/TXT/Markdown and produces structure-aware chunks.

```powershell
Set-Location .\05_document_chunking
& $py .\parse-and-chunk.py .\samples\employee_policy_markdown_sample.md `
      --chunk-size 800 --overlap 100 --quality-report
```

Pre-built outputs for all four formats are already in `outputs/` — these are the
inputs Day 06 expects. Note that without `--output`, the chunk JSON is written
**next to the source file**, not into `outputs/`; pass `--output` to control it:

```powershell
& $py .\parse-and-chunk.py .\samples\employee_policy_text_sample.txt `
      --output .\outputs\employee_policy_txt_chunked.json
```

No model and no network needed — this day is pure parsing.

### 4.6 Day 06 — Embedding and retrieval

Builds a local vector index with `BAAI/bge-small-en-v1.5` and searches it.

**Build the index first** (Days 07 and 08 need it). The first run downloads the
model (~130 MB) and needs internet; afterwards it is fully local:

```powershell
Set-Location .\06_embedding_and_retrieval
& $py -m src.embeddings.build_embeddings `
      ..\05_document_chunking\outputs\employee_policy_md_chunked.json `
      --index-dir .\outputs\embeddings\employee_policy_md_structure
```

This writes `vectors.npz`, `metadata.json` and `manifest.json`. The manifest
records the real dimension, token limit, and any skipped chunks.

Search and evaluate:

```powershell
& $py -m src.retrieval.search --index-dir .\outputs\embeddings\employee_policy_md_structure `
      --query "When is a receipt required?" --top-k 5
& $py -m src.evaluation.evaluate_retrieval --queries .\test_inputs\retrieval_queries.json `
      --index-dir .\outputs\embeddings\employee_policy_md_structure `
      --output .\outputs\reports\md_structure.json
& $py -m pytest -q     # 8 tests, uses a fake model — no download
```

Omit `--query` for an interactive search loop. Use `--no-query-instruction` only
if the index was built with that same option.

### 4.7 Day 07 — RAG pipeline

Retrieval + grounded answer generation with citation validation.

```powershell
Set-Location .\07_rag
& $py -m pytest -q              # 30 tests, mocked — no model or index needed
& $py -m rag.phase5_runner      # scripted cases -> outputs/phase5_rag_test_results.json
```

Live end-to-end run against the Day 06 index and a local model:

```powershell
& $py -m rag.pipeline --index-dir ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure `
      --question "When is a receipt required?"
```

The live integration test is gated behind its own variable:

```powershell
$env:RUN_RAG_INTEGRATION = "1"
& $py -m pytest .\tests -m integration -q
```

`outputs/failure_analysis.md` documents a past run where the index was missing —
useful context if your own run fails the same way.

### 4.8 Day 08 — RAG evaluation

Scores Day 07's answers: retrieval hit, citation validity, and failure class.

```powershell
Set-Location .\08_rag_evaluation
& $py -m pytest -m "not integration" -q    # 17 tests
& $py -m src.evaluator                     # all cases
& $py -m src.evaluator --case-id receipt_numeric_threshold
```

This day resolves Day 07 and Day 06 by path. The defaults are correct for this
repository layout; override only if you moved things:

```powershell
$env:DAY07_PROJECT_DIR = "..\07_rag"
$env:DAY06_INDEX_DIR   = "..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure"
```

The integration test needs the index, a model, **and** its opt-in variable —
without `RUN_DAY08_INTEGRATION=1` it silently reports `skipped`:

```powershell
$env:RUN_DAY08_INTEGRATION = "1"
& $py -m pytest tests/test_integration.py -m integration -v
```

### 4.9 Day 09 — Architecture / fine-tuning decisions

A judgement exercise, not a training run: no GPU and no model. You fill in a
decision card and the scripts validate it.

```powershell
Set-Location .\09_fine_tuning
& $py -m src.scenario_loader --list
& $py -m src.scenario_loader --show S06
& $py -m src.scenario_loader --export-template S01    # writes into submissions/
& $py -m src.decision_evaluator --submission .\submissions\S01_submission.json
& $py -m src.fine_tuning_readiness --export-template .\submissions\fine_tuning_readiness.json
& $py -m src.fine_tuning_readiness --assess .\submissions\fine_tuning_readiness.json
& $py -m pytest -q     # 16 tests
```

### 4.10 Day 10 — Tool calling

A controlled tool-calling assistant: a read-only knowledge lookup and a
write-guarded service request. Writes require an explicit `--allow-write`.

```powershell
Set-Location .\10_tool_calling
& $py -m pytest -q     # 31 tests

# Scripted demos — deterministic, no live model
& $py -m src.assistant --demo lookup    --message "Run the scripted lookup demonstration."
& $py -m src.assistant --demo ambiguous --message "Can you take care of this?"
& $py -m src.assistant --demo write --allow-write --message "Run the scripted write demonstration."

# Live model
& $py -m src.assistant --message "Use the knowledge tool to find the expense claim deadline."
& $py -m src.assistant --allow-write --message "Create a normal-priority database access request for the analytics project."
```

Set `KNOWLEDGE_BACKEND=mock` to use `data/mock_knowledge.json` instead of the Day
06 index — that is what the demos and tests do, and it makes this day runnable
without building an index. Execution logs land in `outputs/logs/`.

The live integration test is gated behind its own variable:

```powershell
$env:RUN_DAY10_INTEGRATION = "1"
$env:KNOWLEDGE_BACKEND = "mock"
& $py -m pytest tests/test_live_integration.py -m integration -q
```

### 4.11 Day 11 — Agents

A bounded ReAct loop (max 10 iterations) over Day 10's tools, on demo leave data.

```powershell
Set-Location .\11_agents
& $py -m pytest -q     # 14 tests, mocked
& $py .\main.py "My user ID is E103. Request leave for Pongal."
& $py .\enterprise_agent.py
```

> **This is the day most likely to look frozen.** It is a real multi-step loop
> against a local model. With `qwen3:4b` on CPU a single question can exceed five
> minutes. Prefer the faster model:
>
> ```powershell
> $env:OLLAMA_MODEL = "llama3.2:3b"
> & $py .\main.py "My user ID is E103. Request leave for Pongal."
> ```

`create_leave_request` only prints — there is no HR integration. Recorded runs
are in `evidence/`.

### 4.12 Day 12 — Reliable agentic workflows

The same leave task as Day 11, but as a **deterministic** workflow: fixed steps,
explicit approval, idempotency keys and an audit trail. Compare the two days
directly — that contrast is the lesson.

```powershell
Set-Location .\12_reliable_agentic_workflows
& $py -m pytest -q     # 12 tests
& $py .\workflow.py --user E104 --festival Diwali --offset 1 --days 2
& $py .\workflow.py --user E104 --festival Diwali --offset 1 --days 2 --create
```

Without `--create` it is a dry run (`CHECK_ONLY`). Re-running the same `--create`
with the same inputs is idempotent.

### 4.13 Day 13 — Agentic engineering

A written design artifact plus a structural validator. No model, no network.

```powershell
Set-Location .\13_agentic_engineering
& $py .\validate_card.py     # -> "Day 13 design card is structurally complete"
& $py -m pytest -q           # 2 tests
```

Edit `design_card.json` and re-run the validator to check your own card.

### 4.14 Day 14 — MCP

Exposes Day 10's read-only lookup through a local MCP server, reached over stdio
by a client.

```powershell
Set-Location .\14_mcp
& $py -m pip install -r .\requirements.txt    # only if you skipped the shared install
& $py -m pytest -q                            # 1 test (in-process client)
& $py .\client.py                             # spawns server.py over stdio
```

`client.py` prints the discovered tool schema, one successful call, and one
deliberate validation failure. **An `INFO ... Tool ... failed` line for the empty
query is expected** — that is the failure case being demonstrated, not a bug.

The server is read-only by design: it exposes the lookup and no write tool.

### 4.15 Day 15 — Evaluations

Golden cases, deterministic hard gates, a scripted baseline, and an LLM judge
that is explicitly **not** yet trusted as a gate.

```powershell
Set-Location .\15_evaluations
& $py -m pytest -q          # 14 tests
& $py .\run_baseline.py     # -> "22 scripted cases; 0 deterministic check failures"
```

The baseline uses scripted model replies and Day 10's mock knowledge. It proves
the *controls* work; it says nothing about live answer quality. For that:

```powershell
& $py .\run_live.py --model llama3.2:3b --case D15-02 --case D15-13   # selected cases
& $py .\run_live.py --model llama3.2:3b                               # all 22
```

The judge requires blind human labels first. Copy
`human_labels_template.csv` to `human_labels.csv`, fill all eight rows **before**
looking at any verdict, then:

```powershell
& $py .\judge.py --model qwen3:4b --labels .\human_labels.csv
```

The script refuses to run until every label is filled — that is intentional.

### 4.16 Day 16 — Observability and tracing

Instruments the Day 10 assistant so every request produces one trace, then uses
the traces to diagnose and fix a defect. Day 10 itself is not modified.

```powershell
Set-Location .\16_observability
& $py -m pytest -q                                      # 77 tests, no model needed

# One case, trace printed as a tree
& $py -m obs.run_traced --case D15-01 --show-trace

# A deliberate fault (all five are off by default)
& $py -m obs.run_traced --case D15-01 --fault flaky_tool --show-trace

# The personal-data case, showing masking
& $py -m obs.run_traced --privacy-case --show-trace

# The fix, before and after, across the suite
& $py -m obs.run_traced --all --fault flaky_tool --retry 0 --out outputs/before.jsonl
& $py -m obs.run_traced --all --fault flaky_tool --retry 2 --out outputs/after.jsonl
& $py -m obs.compare_runs outputs/before.jsonl outputs/after.jsonl   # fixed=8 regressed=0
```

**No LangSmith account or API key is needed** — traces are written locally as
JSONL by default. Set `LANGSMITH_TRACING=true` plus `LANGSMITH_API_KEY` to also
push them to a project; if either is missing the tracer stays local rather than
failing.

The five fault flags are `slow_tool`, `flaky_tool`, `mcp_error`,
`bad_retrieval` and `prompt_bloat`, one at a time, via `--fault` or `FAULT=`.
`slow_tool` makes a run take 3 seconds on purpose — that is the fault, not a
hang. Committed trace evidence is in `evidence/`.

The package here is `obs`, not `src`, because Day 10's package is `src` and a
second one would shadow it on `sys.path`. Run module commands from
`16_observability`, not from inside `obs/`.

---

## 5. The unified hub

One Streamlit app with all sixteen days as pages. **Run it from `ai_engineering`**,
not from `hub/`:

```powershell
Set-Location .\ai_engineering
streamlit run .\hub\app.py
```

Pick the day in the sidebar; set the Ollama host and model there too. The sidebar
shows a red "Ollama not reachable" banner if the server is down — the
model-independent days (04, 05, 09, 13) still work in that state.

When a page fails, the hub shows a one-line error. To see the stack trace:

```powershell
$env:HUB_SHOW_TRACEBACKS = "1"
streamlit run .\hub\app.py
```

---

## 6. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError` | The shared venv is not being used. Call `..\venv\Scripts\python.exe` explicitly rather than bare `python`. |
| `No module named 'mcp'` (Day 14) | Reinstall the shared requirements: `python -m pip install -r ai_engineering\requirements.txt`. |
| `❌ Ollama not reachable` | Start Ollama and confirm with `ollama list`. Check `OLLAMA_HOST` matches the port (default `11434`). |
| A day seems to hang (11, 12, 15) | A real agent loop on a slow model. Set `$env:OLLAMA_MODEL = "llama3.2:3b"` and retry. |
| `Day 07 project not found` | Day 08 cannot locate Day 07. Set `$env:DAY07_PROJECT_DIR = "..\07_rag"`. |
| `index-dir` / vectors not found | Day 06's index is git-ignored and must be built — see [§4.6](#46-day-06--embedding-and-retrieval). |
| Dimension or config mismatch on search | Search with the same `EMBEDDING_MODEL_ID`, normalization and query-instruction setting used to build the index. |
| An integration test says `skipped` | It needs its opt-in variable: `RUN_RAG_INTEGRATION`, `RUN_DAY08_INTEGRATION` or `RUN_DAY10_INTEGRATION` set to `1`. See [§2.4](#24-optional-the-three-live-integration-tests). |
| Model download fails | Check internet, disk space and Hugging Face reachability. Inference itself is local once downloaded. |
| Token-limit skips when embedding | Reduce the Day 05 chunk size. `manifest.json` lists every skipped `chunk_id` and why. |
| `Activate.ps1` is blocked | Skip activation; call `.\venv\Scripts\python.exe` directly. |

---

## 7. What is safe to commit

`.gitignore` already covers these — confirm before committing:

- **Never commit** `.env` (it holds your local host/model configuration).
- Generated and ignored: `venv/`, `__pycache__/`, `.pytest_cache/`, `*.db`,
  Day 06 `outputs/embeddings/`, `outputs/retrieval_results/`, `outputs/reports/`.
- **Do** commit: source, tests, `requirements.txt`, `.env.example`, the Day 05
  chunk outputs under `05_document_chunking/outputs/`, and the recorded evidence
  under each day's `evidence/` and `outputs/` folders.

Check with:

```powershell
git status --short
git check-ignore ai_engineering\.env
```

---

## 8. Reference

Per-day detail lives in each folder's own `README.md` and, where present,
`SETUP.md`. The longer narrative walkthroughs for Days 04–07 are in
[`run-setup-guides/`](run-setup-guides/).

| Day | Folder | Needs a model? | Needs Day 06 index? |
|---|---|---|---|
| 01 | `01_simple_genAI` | yes | no |
| 02 | `02_with_context_level` | yes | no |
| 03 | `03_structured_output` | app yes / tests no | no |
| 04 | `04_enhanced_dev_codex` | no | no |
| 05 | `05_document_chunking` | no | no |
| 06 | `06_embedding_and_retrieval` | no (local BGE) | builds it |
| 07 | `07_rag` | live run only | live run only |
| 08 | `08_rag_evaluation` | integration only | integration only |
| 09 | `09_fine_tuning` | no | no |
| 10 | `10_tool_calling` | live run only | no (`KNOWLEDGE_BACKEND=mock`) |
| 11 | `11_agents` | yes | no |
| 12 | `12_reliable_agentic_workflows` | yes | no |
| 13 | `13_agentic_engineering` | no | no |
| 14 | `14_mcp` | no | no |
| 15 | `15_evaluations` | live/judge only | no |
| 16 | `16_observability` | live diagnosis only | no |
