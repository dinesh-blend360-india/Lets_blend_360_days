# Installation and Setup: Task Management API

This guide assumes you have cloned or downloaded the entire `Lets_blend_360_days`
repository. Use Python 3.11 or newer. The commands below are for Windows PowerShell.

## Quick start with the batch file

Double-click **`run.bat`** in this folder, or run it from a terminal opened in
`04_enhanced_dev_codex`:

```powershell
.\run.bat
```

It finds the repository root automatically, creates or repairs the shared `venv`
if needed, installs `ai_engineering/requirements.txt`, and starts the API.
Open **http://127.0.0.1:8000/docs**. Press **Ctrl+C** to stop it; if Windows asks
`Terminate batch job (Y/N)?`, enter `Y`.

Python 3.11 or newer must already be installed. Internet access may be needed
for dependency installation. To prepare the environment without starting the server:

```powershell
.\run.bat --check
```

If port 8000 is occupied, choose another port:

```powershell
.\run.bat 8001
```

Then open `http://127.0.0.1:8001/docs`.

The manual steps below are an alternative to the batch file.

### macOS and Linux

`run.bat` is a Windows batch file and will not run natively on macOS or Linux.
The FastAPI application itself is cross-platform because it uses Python, FastAPI,
and SQLite. On macOS/Linux, run the equivalent commands from the repository root:

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r ./ai_engineering/requirements.txt
./venv/bin/python -m uvicorn task_api.main:app --app-dir ./ai_engineering/04_enhanced_dev_codex --reload
```

Then open `http://127.0.0.1:8000/docs`. Run tests with:

```bash
./venv/bin/python -m pytest ./ai_engineering/04_enhanced_dev_codex/tests -v
```


## 1. Open the repository root

Open a terminal in `Lets_blend_360_days`, which contains `ai_engineering`:

```text
Lets_blend_360_days/
├── ai_engineering/
│   ├── requirements.txt
│   └── 04_enhanced_dev_codex/
└── venv/                     # Created locally in the next step
```

Run every command below from this root folder.

## 2. Create a local Python environment

```powershell
python --version
python -m venv venv
```

Confirm the version is 3.11 or newer. If Windows does not recognize `python`,
install Python and reopen your terminal; you can also use `py -3.11` in place
of `python` if the Python launcher is available.

If you already have a working `venv`, reuse it. If it points to a missing Python
installation, repair it with a working interpreter:

```powershell
python -m venv --upgrade venv
```

The following commands use the environment's Python directly, so activation
and PowerShell execution-policy changes are unnecessary.

## 3. Install dependencies

```powershell
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
```

Dependencies are recorded in this shared requirements file, which also includes
packages for the repository's other exercises. SQLite is included with Python
and needs no separate installation.

## 4. Start the API

```powershell
.\venv\Scripts\python.exe -m uvicorn task_api.main:app --app-dir .\ai_engineering\04_enhanced_dev_codex --reload
```

Open **http://127.0.0.1:8000/docs** to try the endpoints. Keep this terminal
running; press **Ctrl+C** to stop the server.

If port 8000 is occupied, append `--port 8001` and open
`http://127.0.0.1:8001/docs` instead.

## 5. Create your first task

In the browser's API documentation, open **POST /tasks**, select **Try it out**,
and submit:

```json
{
  "title": "My first task",
  "description": "Check the local API",
  "status": "todo"
}
```

The response should have status **201** and include a generated `id` and
`created_at`. Use **GET /tasks** to list tasks. Allowed statuses are `todo`,
`in_progress`, and `done`.

## 6. Run automated tests

Open another terminal in the repository root:

```powershell
.\venv\Scripts\python.exe -m pytest .\ai_engineering\04_enhanced_dev_codex\tests -v
```

Tests use temporary databases and include persistence across server restarts.
See [VERIFICATION.md](VERIFICATION.md) for previously recorded test results.

## Database and optional configuration

Startup creates `ai_engineering/04_enhanced_dev_codex/data/tasks.db` automatically.
Tasks survive restarts. No API keys or `.env` file are required for this API.

To choose a different database, set this before starting the server:

```powershell
$env:TASK_DB_PATH = 'data/custom-tasks.db'
```

Relative database paths resolve against `04_enhanced_dev_codex`. You can alternatively
add `TASK_DB_PATH=data/custom-tasks.db` to your local `ai_engineering/.env`;
the process environment takes precedence.

The repository ignores the local `venv`, `.env` files, and this API's `data`
directory. After cloning on another machine, create its environment and install
the shared requirements again; the local task database is not included in Git.

See [README.md](README.md) for the full API contract and architecture.
