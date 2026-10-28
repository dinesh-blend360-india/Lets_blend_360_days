# Day 10 setup and running guide

The examples use Windows PowerShell. In Command Prompt, open the same folder with:

```cmd
cd /d C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\10_tool_calling
```

## 1. Open the project

```powershell
Set-Location C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\10_tool_calling
```

## 2. Activate or create Python

Check the existing environment:

```powershell
& ..\..\venv\Scripts\Activate.ps1
python --version
```

If it is broken, install Python 3.10+ and create a local environment:

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1
```

## 3. Install shared requirements

Day 10 has no project-level requirements file:

```powershell
python -m pip install -r ..\requirements.txt
```

The shared file already declares `ollama`, `sentence-transformers`, `numpy`, and `pytest`; no new dependency was needed.

## 4. Configure the application

```powershell
Copy-Item .env.example .env
```

Day 10 reads environment variables directly; it does not automatically load `.env`. Set the values in the shell or load them using your normal environment workflow:

```powershell
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "qwen2.5:3b"
$env:KNOWLEDGE_BACKEND = "day07"
$env:ALLOW_SERVICE_REQUEST_CREATE = "false"
```

The model name is an example, not proof that it is installed or supports tools.

## 5. Verify Ollama and the model

```powershell
ollama --version
ollama list
```

Select an installed model with native tool-call support. If none is installed, choose and download one manually; Day 10 never downloads a model automatically.

Verify the Day 06 index used by Day 07:

```powershell
Get-ChildItem ..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure
```

It should contain `manifest.json`, `metadata.json`, and `vectors.npz`.

## 6. Start the assistant

Interactive, read-only actor:

```powershell
python -m src.assistant
```

One read request:

```powershell
python -m src.assistant --message "Use the knowledge lookup tool to find the expense claim deadline."
```

## 7. Propose and confirm a simulated action

Grant only this CLI invocation simulated-create permission:

```powershell
python -m src.assistant --allow-write --message "Create a normal-priority database access request because access is needed for the analytics project."
```

Review the displayed title, priority, and description. Type exactly:

```text
CONFIRM
```

The resulting local JSON record appears under `outputs\actions`.

## 8. Reject an action

Run the same command but type `NO`, press Enter, or provide anything other than `CONFIRM`:

```powershell
python -m src.assistant --allow-write --message "Create a normal-priority database access request because access is needed for the analytics project."
```

Confirm no new record was created:

```powershell
Get-ChildItem outputs\actions\*.json
```

## 9. Explicit offline mock knowledge mode

Use this only for a clearly labelled demonstration when Day 07 dependencies are unavailable:

```powershell
$env:KNOWLEDGE_BACKEND = "mock"
python -m src.assistant --message "Use the knowledge lookup tool to find the expense deadline."
```

Responses identify the backend as `mock` and use `mock_` chunk IDs.

To avoid requiring Ollama as well, use the deterministic scripted demo model:

```powershell
python -m src.assistant --demo lookup --message "Run the scripted lookup demonstration."
python -m src.assistant --demo ambiguous --message "Can you take care of this?"
python -m src.assistant --demo write --allow-write --message "Run the scripted write demonstration."
```

These commands are visibly labelled mocks. The scripted write continues to require `CONFIRM`.

## 10. Run tests

Mocked tests only; no model download or Ollama service is needed:

```powershell
python -m pytest -m "not integration" -q
```

Optional live test, only after `ollama list` confirms a suitable model:

```powershell
$env:RUN_DAY10_INTEGRATION = "1"
python -m pytest tests\test_live_integration.py -m integration -v
```

## 11. Inspect actions and logs

```powershell
Get-ChildItem outputs\actions
Get-Content outputs\logs\tool_execution.jsonl
```

Each JSONL event includes real measured duration for that execution. Logs intentionally omit descriptions and retrieved document text.

## Troubleshooting

- **Python unavailable:** install Python 3.10+ and recreate the environment. A copied virtual environment may point to a Python installation that no longer exists.
- **Ollama unavailable:** start Ollama, verify `OLLAMA_BASE_URL`, and run `ollama list`.
- **Model never calls tools:** verify that the selected installed model supports native Ollama tool calling; try a direct request explicitly asking it to use the named tool.
- **Model timeout:** increase `OLLAMA_TIMEOUT_SECONDS` only after checking service health and local resource use.
- **Retrieval import/model error:** verify shared requirements and the Day 06 index. Use explicit mock mode only as a labelled fallback.
- **Validation error:** inspect the returned error code; unknown fields, empty text, invalid enums, and out-of-range `top_k` are rejected.
- **Permission denied:** pass `--allow-write` for this local demonstration or set `ALLOW_SERVICE_REQUEST_CREATE=true`. Confirmation cannot override denial.
- **Cancelled:** type exactly `CONFIRM`; all other inputs reject the proposal.
- **Round limit:** simplify the request or inspect why the model keeps requesting tools; do not raise the limit without diagnosing the loop.
- **Persistence failure:** verify that `outputs\actions` is writable. The application reports failure and removes temporary files.

