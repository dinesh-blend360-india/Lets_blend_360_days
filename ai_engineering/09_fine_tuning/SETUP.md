# Day 09 setup and running guide

All commands below use Windows PowerShell.

## 1. Open the project

```powershell
Set-Location C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\09_fine_tuning
```

## 2. Check Python

```powershell
python --version
```

Python 3.10 or newer is recommended. If `python` is unavailable but the launcher exists, use `py -3.11` when creating the environment.

## 3. Create and activate an environment

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1
python --version
```

## 4. Install the shared dependencies

Day 09 intentionally has no local `requirements.txt`. It uses the common AI Engineering file:

```powershell
python -m pip install -r ..\requirements.txt
```

The Day 09 implementation itself uses the Python standard library. `pytest` from the shared file is needed for tests. No machine-learning library, model download, API key, or GPU is needed for this exercise.

## 5. List and inspect scenarios

```powershell
python -m src.scenario_loader --list
python -m src.scenario_loader --show S01
python -m src.scenario_loader --show S08
```

## 6. Export and record a decision

Create a new template—the command refuses to overwrite an existing submission:

```powershell
python -m src.scenario_loader --export-template S01
```

Or choose an explicit destination:

```powershell
python -m src.scenario_loader --export-template S06 --output submissions\my_s06_decision.json
```

Open the generated JSON and complete every empty value. Use one of:

```text
PROMPT_CONTEXT
RAG
FINE_TUNING
COMBINATION
NO_LLM
DECISION_DEFERRED
```

S06 requires `staged_approach`. S08 requires `DECISION_DEFERRED` until discovery resolves the unknowns.

## 7. Evaluate a submission

```powershell
python -m src.decision_evaluator --submission submissions\S01_submission.json
```

Preview JSON without writing a historical report:

```powershell
python -m src.decision_evaluator --submission submissions\S01_submission.json --no-write
```

## 8. Assess fine-tuning readiness

```powershell
python -m src.fine_tuning_readiness --export-template submissions\fine_tuning_readiness.json
```

After documenting each status and reason:

```powershell
python -m src.fine_tuning_readiness --assess submissions\fine_tuning_readiness.json
```

## 9. Run tests

```powershell
python -m pytest -q
```

Tests use temporary files and deterministic fixtures. They do not call an API or download a model.

## 10. Find outputs

```powershell
Get-ChildItem outputs\run_history
Get-Content outputs\reports\latest_report.md
```

Each run contains:

```text
outputs\run_history\<run-id>\result.json
outputs\run_history\<run-id>\report.md
outputs\run_history\<run-id>\manifest.json
```

## Troubleshooting

- **`python` and `py` are unavailable:** install Python 3.10+ and recreate the environment. A copied virtual environment may point to a Python installation that no longer exists.
- **Invalid architecture:** use exactly one of the six uppercase labels listed above.
- **Missing submission field:** compare your JSON with a freshly exported template.
- **S06 validation error:** add a concrete sequence to `staged_approach` beginning with a measured RAG baseline.
- **S08 validation error:** select `DECISION_DEFERRED` and document discovery instead of guessing an architecture.
- **Existing template or run:** templates and historical runs are protected from accidental overwrite; choose another filename or allow a new timestamped run.
- **Low score despite reasonable prose:** inspect matched rubric keywords in `result.json`; deterministic lexical scoring is intentionally limited and should be paired with human review.

