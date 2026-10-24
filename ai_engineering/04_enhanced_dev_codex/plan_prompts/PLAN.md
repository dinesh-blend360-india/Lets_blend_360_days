# Minimal Task Management API

## Architecture and project structure

Build in the existing `ai_engineering/4_enhanced_dev` folder:

```text
4_enhanced_dev/
├── task_api/
│   ├── __init__.py
│   ├── main.py        # App factory, startup, routes, responses
│   ├── schemas.py     # Pydantic request/response models and statuses
│   └── database.py    # SQLite initialization and CRUD queries
├── tests/
│   └── test_tasks.py
├── data/              # Runtime database, ignored by Git
└── README.md
```

Use Python’s standard-library `sqlite3` directly: one table and a few parameterized queries do not require an ORM. FastAPI supports choosing the database library independently. [FastAPI documentation](https://fastapi.tiangolo.com/tutorial/sql-databases/)

Use synchronous routes, short-lived connections, explicit transactions, and an app factory accepting a database path for isolated tests. Initialize the table during application startup.

## Data flow and API behavior

Request JSON → Pydantic validation → route → parameterized SQLite query → response model → JSON.

Each task contains:

- `id`: server-generated integer primary key.
- `title`: required string, trimmed; reject empty or whitespace-only values.
- `description`: optional string, default `null`.
- `status`: exactly `todo`, `in_progress`, or `done`; default `todo`.
- `created_at`: server-generated UTC timestamp, returned in ISO 8601 format.

Reject incorrect field types and unknown fields, including client-supplied IDs and timestamps. Pydantic supports strict validation and custom validators. [Pydantic documentation](https://docs.pydantic.dev/latest/concepts/validators/)

| Endpoint | Successful response |
|---|---|
| `POST /tasks` | `201`, created task |
| `GET /tasks` | `200`, array ordered by ascending ID; `[]` when empty |
| `GET /tasks/{task_id}` | `200`, task |
| `PATCH /tasks/{task_id}` | `200`, updated task |
| `DELETE /tasks/{task_id}` | `204`, empty body |

PATCH changes only supplied fields. Omitted fields remain unchanged; `description: null` clears the description. Explicit null titles/statuses and empty PATCH objects return `422`. ID and creation timestamp remain immutable.

Invalid bodies, statuses, titles, or non-positive/non-integer path IDs return `422` with field-specific errors. Valid IDs that do not exist return `404` with `{"detail":"Task not found"}`. Status transitions are unrestricted.

## Storage, environment, and dependencies

Default storage is `4_enhanced_dev/data/tasks.db`, resolved independently of the working directory. An optional `TASK_DB_PATH` setting can override it through the environment or existing `ai_engineering/.env`; process environment takes precedence. Do not print `.env` contents or change unrelated settings.

File-backed SQLite survives restarts and requires no database service. In-memory SQLite loses data when its connection closes and cannot satisfy persistence. SQLite permits limited concurrent writes, which is suitable for this local API.

Keep all dependency records in `ai_engineering/requirements.txt`:

- Add `fastapi`: routing, validation integration, OpenAPI documentation.
- Add `uvicorn`: local ASGI server, without optional extras.
- Reuse `pydantic`: request and response validation.
- Reuse `pytest` and `httpx`: automated API tests.
- Reuse `python-dotenv`: optional existing `.env` configuration.
- `sqlite3` needs no installation.

Repair or recreate the existing repository-level `venv`, as selected. Its configured Python executable is missing, and no replacement was found on PATH; a working Python interpreter is a prerequisite. Record tested direct dependency versions without changing unrelated requirements.

## Automated tests and verification

Use temporary file-backed databases, isolated from the user’s database.

Cover:

- Creation defaults, generated IDs, and UTC timestamps.
- Listing, retrieval, partial updates, and deletion.
- Title trimming; empty, whitespace-only, null, and incorrectly typed titles.
- Every allowed status; invalid and null statuses.
- Optional descriptions and clearing them with PATCH.
- Unknown fields, immutable fields, empty PATCH, and invalid IDs.
- `404` for missing tasks and retrieval after deletion.
- Preservation of omitted fields and creation timestamps.
- Persistence across two fresh app instances using the same database.
- Persistence across two separate Python processes using the same database.
- Startup initialization without deleting existing records.

After approval, implement incrementally, run the tests, review the diff, and update the README with setup, launch, test commands, examples, status values, and database configuration.

Planned commands from the repository root:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
.\venv\Scripts\python.exe -m pytest .\ai_engineering\4_enhanced_dev\tests -v
.\venv\Scripts\python.exe -m uvicorn task_api.main:app --app-dir .\ai_engineering\4_enhanced_dev --reload
```

Record actual commands, exit codes, test counts, changed files, and unexpected behavior. Preserve existing unrelated changes. No implementation or package installation has occurred yet.
