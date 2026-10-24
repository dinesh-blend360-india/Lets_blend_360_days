# Task Management API

**Recommended:** run `run.bat` from this folder for the easiest setup and startup flow. It prepares the shared environment, installs dependencies, and launches the API; see [SETUP.md](SETUP.md) for the complete guide.

A minimal local REST API using FastAPI, Pydantic, and Python's built-in SQLite
driver. No authentication, frontend, cloud services, or external integrations.

## Setup

Use Python 3.11 or newer. Run commands from `Lets_blend_360_days`, the repository
root containing `ai_engineering` and the shared `venv`.

Create the environment if needed:

```powershell
python -m venv venv
```

If the existing environment refers to a missing Python installation, repair it
with a working interpreter:

```powershell
python -m venv --upgrade venv
```

Install dependencies and launch the API:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
.\venv\Scripts\python.exe -m uvicorn task_api.main:app --app-dir .\ai_engineering\4_enhanced_dev_codex --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is at
`http://127.0.0.1:8000/docs`; the OpenAPI schema is at `/openapi.json`.
All project dependencies are recorded in the shared `ai_engineering/requirements.txt`.
FastAPI handles routing and OpenAPI, Pydantic validates payloads, Uvicorn serves the
app, python-dotenv reads optional configuration, and pytest/httpx provide tests.
SQLite needs no additional package. The shared requirements also include packages
used by other exercises.

## API contract

Tasks contain an automatically generated integer `id`, a required non-empty
`title`, an optional `description`, a `status`, and a server-generated UTC
`created_at` timestamp in ISO 8601 format.

Allowed statuses are **`todo`**, **`in_progress`**, and **`done`**. New tasks default
to `todo`; transitions between any of these values are allowed. Titles are trimmed
before storage. Strings are required for titles and non-null descriptions.

| Endpoint | Success | Body |
| --- | --- | --- |
| `POST /tasks` | 201 | Created task |
| `GET /tasks` | 200 | Tasks ordered by ascending ID; `[]` if empty |
| `GET /tasks/{task_id}` | 200 | Task |
| `PATCH /tasks/{task_id}` | 200 | Updated task |
| `DELETE /tasks/{task_id}` | 204 | Empty |

POST requires `title`; `description` defaults to `null`. PATCH changes only
supplied fields. Send `description: null` to clear it. Empty PATCH objects and
explicit null titles/statuses are rejected. IDs and timestamps cannot be supplied
or modified; unknown fields are rejected.

Invalid JSON, missing required fields, incorrect types, blank titles, invalid
statuses, and non-positive/non-integer path IDs return **422** with meaningful
validation details identifying the field. Requests with a valid payload and a
nonexistent task ID return **404** with `{"detail":"Task not found"}`.

Example PowerShell requests while the server is running:

```powershell
$task = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/tasks -ContentType application/json -Body '{"title":"Write tests","description":"Cover persistence"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/tasks
Invoke-RestMethod -Uri "http://127.0.0.1:8000/tasks/$($task.id)"
Invoke-RestMethod -Method Patch -Uri "http://127.0.0.1:8000/tasks/$($task.id)" -ContentType application/json -Body '{"status":"done"}'
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/tasks/$($task.id)"
```

## Architecture and persistence

`task_api/main.py` owns the app factory, startup, configuration, and routes.
`schemas.py` defines the request/response models. `database.py` owns the table and
parameterized SQL queries. The flow is JSON request → Pydantic validation → route
→ SQLite transaction → response model → JSON response.

Each synchronous database operation creates and closes its own connection.
Writes commit on success and roll back on failure. PATCH performs its
read/merge/write in one transaction to preserve omitted fields under concurrent
updates. Startup creates the table if absent and preserves existing records.

By default, SQLite stores tasks in `4_enhanced_dev_codex/data/tasks.db`, independently
of the working directory. The directory is created on startup and ignored by Git.
Tasks survive application and process restarts. In-memory SQLite loses its contents
when the connection closes and is unsuitable for this persistence requirement.
File-backed SQLite needs no separate service, but serializes writes; it suits
this small local application.

Optionally set `TASK_DB_PATH` in the process environment or the existing
`ai_engineering/.env`; process environment takes precedence. Relative configured
paths resolve against `4_enhanced_dev_codex`. An empty value uses the default path.
Existing unrelated `.env` settings are neither modified nor logged.

```powershell
$env:TASK_DB_PATH = 'data/custom-tasks.db'
```

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest .\ai_engineering\4_enhanced_dev_codex\tests -v
```

Tests use temporary file-backed databases, never the default user database.
They cover CRUD, defaults, ordering, UTC timestamps, trimming, allowed statuses,
validation errors, immutable fields, missing IDs, clearing descriptions, preservation
of omitted fields, SQL parameterization, OpenAPI documentation, and configuration.
Persistence tests recreate the app and use two independent Python processes against
the same database file. A live Uvicorn test also sends real HTTP requests and
restarts the server against its temporary database.

The tested Starlette version emits a deprecation warning for TestClient's use of
httpx. This does not fail the tests; the existing shared httpx dependency is retained.

Actual execution commands and results are recorded in `VERIFICATION.md`.
