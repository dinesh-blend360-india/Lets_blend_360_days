# Day 04 — A Task Management API, built with an AI coding assistant

| | |
|---|---|
| **Folder** | `04_enhanced_dev_codex/` — `task_api/`, `tests/`, `plan_prompts/`, `assignments/`, `run.bat`, `README.md`, `SETUP.md`, `VERIFICATION.md` |
| **Command** | `.\run.bat` (easiest) or `uvicorn` (below) |
| **Needs** | Python 3.11+. **No model, no Ollama, no internet** (after installing packages). |
| **Time** | 1–2 hours to run and explore; longer if you build your own version |
| **Depends on** | Nothing |

---

## 1. What you are learning

Day 04 is a change of subject. Days 01–03 are about *models*. Day 04 is about
the **ordinary software engineering that every AI product still needs**, and
about **how to work with an AI coding assistant** without losing control of the
result.

**The software.** A small REST API for tasks (create, list, read, update,
delete) with:

- **FastAPI** — routing, plus automatic interactive documentation at `/docs`.
- **Pydantic** — validates every request *before* your code sees it (the same
  idea as Day 03, now at an API boundary).
- **SQLite** (Python's built-in `sqlite3`) — a file database; tasks survive a
  restart.
- **Parameterized SQL** — values are passed separately from the query text, which
  is how you avoid SQL injection.
- **HTTP semantics** — `201` created, `204` no content, `404` not found, `422`
  invalid input. Knowing which code means what is half of API design.
- **Tests that never touch real data** — each test uses a temporary database.

**The method.** The folder name says it: it was built with a coding assistant.
`plan_prompts/PLAN.md` is the *plan* given to the assistant before any code —
architecture, behaviour rules, edge cases, even which files to create.
`VERIFICATION.md` is the *evidence* that came back. The skill being practised is
**specify precisely → let the assistant build → verify independently**, not
"ask the AI and hope".

## 2. Setup

Nothing model-related. You need the shared environment ([one-time setup](README.md#23-create-the-shared-virtual-environment))
which already installs `fastapi` and `uvicorn`.

Check:

```powershell
& $py -c "import fastapi, uvicorn, pydantic, sqlite3; print('fastapi', fastapi.__version__)"
```

## 3. Run

### Easiest: the batch file

```powershell
Set-Location "$ai\04_enhanced_dev_codex"
.\run.bat --check        # installs/verifies dependencies, prints "Setup check passed.", does NOT start the server
.\run.bat                # starts on http://127.0.0.1:8000
.\run.bat 8080           # or choose a port
```

`run.bat` finds Python 3.11+, creates or repairs the shared `venv` if needed,
installs `requirements.txt` and starts the server with auto-reload. It pauses on
an error so a double-clicked window does not vanish. Press `Ctrl+C` to stop.

### Manual

```powershell
Set-Location $ai
& $py -m uvicorn task_api.main:app --app-dir "$ai\04_enhanced_dev_codex" --reload
```

Open **<http://127.0.0.1:8000/docs>** — an interactive page where you can try
every endpoint with a button. The raw schema is at `/openapi.json`.

### Tests

```powershell
& $py -m pytest "$ai\04_enhanced_dev_codex\tests" -v
```

### Use it from PowerShell

With the server running, in a second window (remember `$py`, `$ai` are per-window):

```powershell
$task = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/tasks -ContentType application/json -Body '{"title":"Write tests","description":"Cover persistence"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/tasks
Invoke-RestMethod -Uri "http://127.0.0.1:8000/tasks/$($task.id)"
Invoke-RestMethod -Method Patch  -Uri "http://127.0.0.1:8000/tasks/$($task.id)" -ContentType application/json -Body '{"status":"done"}'
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/tasks/$($task.id)"
```

## 4. What to test

Do each one in `/docs` ("Try it out") **and** read the response code.

- [ ] **Create** with only a title → `201`; `status` defaults to `todo`.
- [ ] **Title with spaces around it** (`"  Write tests  "`) → stored trimmed.
- [ ] **Blank title** (`"   "`) → `422` with a message naming the `title` field.
- [ ] **Invalid status** (`"blocked"`) → `422` listing the three allowed values.
- [ ] **Unknown field** (`"id": 5` or `"created_at": …`) → `422` (they cannot be supplied).
- [ ] **Update only the status** (`PATCH`) → the other fields are unchanged.
- [ ] **Clear a description** with `"description": null` → it becomes `null`.
- [ ] **Empty PATCH body `{}`** → `422` "Provide at least one field to update".
- [ ] **Read a task that does not exist** (`/tasks/999`) → `404 {"detail":"Task not found"}`.
- [ ] **Bad ID** (`/tasks/0`, `/tasks/abc`) → `422` (not `404`) — a different problem.
- [ ] **Delete** → `204` and an empty body; delete it again → `404`.
- [ ] **Restart the server** (Ctrl+C, start again) → your tasks are still there.
- [ ] **Look at `/openapi.json`** and find your endpoints.

For the tests, read `tests/test_tasks.py`, then try **breaking the code on
purpose** (e.g. remove the title trimming in `schemas.py`) and see which tests
catch it. A test that never fails is not telling you anything.

## 5. What to expect

Real responses (from running the server against a throwaway database):

| Request | Response |
|---|---|
| `POST /tasks` `{"title":"  Write tests  ","description":"Cover persistence"}` | `201` `{"id":1,"title":"Write tests","description":"Cover persistence","status":"todo","created_at":"2026-10-29T12:33:17.296402Z"}` |
| `POST /tasks` `{"title":"   "}` | `422` `{"detail":[{"type":"string_too_short","loc":["body","title"],"msg":"String should have at least 1 character",…}]}` |
| `POST /tasks` `{"title":"x","status":"blocked"}` | `422` `…"msg":"Input should be 'todo', 'in_progress' or 'done'"…` |
| `GET /tasks` | `200` an array, ascending by `id`; `[]` when empty |
| `PATCH /tasks/1` `{"status":"done"}` | `200` the full updated task |
| `PATCH /tasks/1` `{}` | `422` `…"msg":"Value error, Provide at least one field to update"…` |
| `GET /tasks/999` | `404` `{"detail":"Task not found"}` |
| `GET /tasks/0` | `422` `…"msg":"Input should be greater than 0"…` |
| `DELETE /tasks/1` | `204` (empty body) |

Tests: **`64 passed`** (about 5–10 s), with one deprecation warning from the web
framework's test client, which does not fail anything.

The database file appears at `04_enhanced_dev_codex/data/tasks.db`. It is
git-ignored (`*.db`), so your tasks are never committed.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `run.bat` says "Python 3.11 or newer is required" | Older/missing Python | Install 3.11+; or check `py -3 --version` |
| `[Errno 10048]` / "address already in use" | Port 8000 taken (an older server) | Close it, or `.\run.bat 8080` |
| `Error loading ASGI app. Could not import module "task_api.main"` | Wrong `--app-dir` | Point `--app-dir` at the `04_enhanced_dev_codex` folder |
| Changes not showing | `--reload` not on, or the server never restarted | Use `--reload`, or restart |
| `Invoke-RestMethod` fails with a long red error on 422 | PowerShell hides the body | Use `/docs`, or catch the exception and read `$_.ErrorDetails.Message` |
| Tasks vanish between runs | `TASK_DB_PATH` points somewhere new | Unset it, or note the path in use |
| Pytest warns about `httpx` / Starlette | Known, harmless | Ignore |

## 7. Learn more

- **FastAPI tutorial** — path/query/body parameters, dependency injection,
  status codes. <https://fastapi.tiangolo.com>
- **HTTP status codes** (MDN "HTTP response status codes").
- **REST resource design** — nouns, idempotent methods, `PUT` vs `PATCH`.
- **SQL injection** — find the one parameterized query in `database.py` and
  imagine it built with string formatting instead.
- **Transactions and isolation** in SQLite; why file-backed SQLite serialises
  writes.
- **SQLAlchemy + Alembic** — what you would add for migrations and an ORM.
- **Writing a good spec for an AI assistant:** read `PLAN.md` as an example;
  note how it states rejected behaviours ("reject unknown fields") as precisely
  as accepted ones.

## 8. What you might be missing

- **This is the one day with no AI model in it, and it is the foundation for
  Days 10–14.** Tool calling, MCP and workflows are all "an API with a contract
  plus validation". Do not skip it.
- **`plan_prompts/prompts.txt` is empty (0 bytes).** The *plan* is in `PLAN.md`;
  the prompts you actually typed to the assistant are not recorded. If your
  assignment asks you to show your prompting, **this is where to put them** —
  and it is a good habit regardless.
- **`assignments/assignment_1/` is the Day 03 validation code copied and
  extended**, with a one-line readme. It is not part of the API.
- **`PLAN.md` mentions `4_enhanced_dev/`** — the folder's earlier name. It is a
  historical record of the original instruction, so it was left as written. The
  real folder is `04_enhanced_dev_codex/`.
- **`VERIFICATION.md` is a record of what happened on 14 October on someone's
  machine.** It is evidence, not a promise. Your own `pytest` run is the real
  check.
- **There is no authentication, no authorization, no pagination, no filtering,
  no rate limiting and no CORS configuration.** A task list for one local user.
  Any real API would need all of these.
- **IDs and timestamps are server-controlled** — a design decision worth
  defending (never trust the client for either).
- **Reading AI-written code is a skill.** Whoever wrote it, *you* are
  accountable for it. A useful exercise: pick one function in `task_api/` and
  explain every line aloud.
- **A single shared `venv` for the whole repo** means a package you install for
  one day is present for all. Convenient for learning, not how production
  projects are isolated.
- **The tests start a real server** (twice) in one test, to prove persistence
  across restarts. That is why the suite is slower than a pure unit suite.

## 9. Where this leads

Day 10 builds an assistant whose "tools" are exactly this kind of validated,
permissioned interface. Day 14 wraps a tool in a standard protocol. The habit of
specifying behaviour, including what must be *rejected*, carries straight through.
