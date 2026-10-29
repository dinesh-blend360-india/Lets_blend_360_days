# AI Engineering Day Setup Guide

This is the shared setup guide for agents working in the `ai_engineering` days
inside `Lets_blend_360_days`.

## Instructions for an agent

1. Treat `Lets_blend_360_days` as the repository root. Confirm that this guide
   is at `ai_engineering/day setup guide.md` before running setup commands.
2. Read the day-specific README and setup guide before changing or running that
   day's code.
3. Preserve unrelated working-tree changes, `.env` files, databases, and user
   data. Never print or copy secrets from `.env`.
4. Reuse the repository-level `venv` at `Lets_blend_360_days/venv` when it is
   available. Do not create a separate environment for each day unless the
   user explicitly requests it.
5. Keep dependency changes in the shared
   `ai_engineering/requirements.txt` unless a day-specific guide explicitly
   documents another dependency file.
6. Run the smallest relevant tests after setup and report the exact command and
   result. Do not claim success without running the command.

## Shared repository layout

```text
Lets_blend_360_days/
├── ai_engineering/
│   ├── requirements.txt
│   ├── day setup guide.md
│   ├── 01_simple_genAI/
│   ├── 02_with_context_level/
│   ├── 03_structured_output/
│   ├── 04_enhanced_dev_codex/
│   └── 05_document_chunking/
└── venv/                         # Local, normally ignored by Git
```

## Windows setup

Open PowerShell in the repository root and verify Python:

```powershell
python --version
```

Python 3.11 or newer is expected. Create or repair the shared environment if
needed, then install the recorded dependencies:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
```

If the Python launcher is installed, `py -3 -m venv --upgrade venv` can repair
an existing environment whose configured Python executable is missing.

## Day 4 Task Management API

For the API day, an agent must read these files before operating the app:

- [`04_enhanced_dev_codex/SETUP.md`](04_enhanced_dev_codex/SETUP.md) — complete
  setup, run, testing, folder-only, and macOS/Linux instructions.
- [`04_enhanced_dev_codex/README.md`](04_enhanced_dev_codex/README.md) — API
  contract, storage behavior, and endpoint examples.
- [`04_enhanced_dev_codex/run.bat`](04_enhanced_dev_codex/run.bat) — Windows
  automation that creates or repairs the shared environment, installs
  dependencies, and starts Uvicorn.

When working from the API folder, use the launcher:

```powershell
Set-Location .\ai_engineering\04_enhanced_dev_codex
.\run.bat --check
.\run.bat
```

Use `.\run.bat 8001` if port 8000 is busy. Open
`http://127.0.0.1:8000/docs` after startup. Run API tests from the repository
root:

```powershell
.\venv\Scripts\python.exe -m pytest .\ai_engineering\04_enhanced_dev_codex\tests -v
```

The API stores its default SQLite database under
`ai_engineering/04_enhanced_dev_codex/data/`. That runtime data is ignored by
Git and should not be deleted as part of ordinary setup.

## macOS/Linux setup

`run.bat` is Windows-only. The API itself runs on macOS/Linux with the shared
environment:

```bash
cd Lets_blend_360_days
python3 -m venv venv
./venv/bin/python -m pip install -r ./ai_engineering/requirements.txt
./venv/bin/python -m uvicorn task_api.main:app \
  --app-dir ./ai_engineering/04_enhanced_dev_codex --reload
```

Run its tests with:

```bash
./venv/bin/python -m pytest ./ai_engineering/04_enhanced_dev_codex/tests -v
```

## Completion report

After setup or a change, report:

- Which day and directory were used.
- Whether the shared environment already existed or was created/repaired.
- The exact dependency and test commands run.
- Test counts, exit codes, warnings, and any unexpected behavior.
- Changed files, while noting unrelated pre-existing changes.

For Day 4, `04_enhanced_dev_codex/VERIFICATION.md` contains the existing command
and test record; treat it as historical evidence and rerun checks when code or
environment state has changed.
