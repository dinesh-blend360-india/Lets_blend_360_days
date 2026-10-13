# Execution record

Implementation and verification performed on 14 October 2026 (Asia/Calcutta).
Commands below used PowerShell from
`C:\workspace\IDC-on-boarding-training\Lets_blend_360_days` unless noted.

## Dependency installation and tests

```powershell
./venv/Scripts/python.exe --version
./venv/Scripts/python.exe -m pip install -r ./ai_engineering/requirements.txt
./venv/Scripts/python.exe -m pytest ./ai_engineering/4_enhanced_dev_codex/tests -v
./venv/Scripts/python.exe -m pip check
./venv/Scripts/python.exe -c "import importlib.metadata as m; print('\n'.join(n + '==' + m.version(n) for n in ('fastapi','uvicorn','pydantic','pytest','httpx','python-dotenv')))"
./venv/Scripts/python.exe -m pip install -r ./ai_engineering/requirements.txt --quiet
```

| Execution | Exit code | Actual outcome |
| --- | --- | --- |
| Python version, outside sandbox | 0 | Python 3.11.9 |
| Initial requirements installation | 0 | Installed fastapi 0.143.0, annotated-doc 0.0.5, opentelemetry-api 1.45.1; other requirements already satisfied |
| First pytest run | 0 | 57 passed, 1 warning in 9.80s |
| Initial pip check | 0 | No broken requirements found |
| Dependency version inspection | 0 | Confirmed the six direct dependency versions pinned in requirements.txt |
| Requirements installation after direct version pins | 0 | Success; pip printed only its update notice |
| Second pytest run, after adding live Uvicorn verification | 0 | 58 passed, 1 warning in 15.51s |
| Final pytest run, after oversized-ID guards and regression cases | 0 | 64 passed, 1 warning in 9.51s |
| Final requirements installation, including downloaded transitive package records | 0 | Success; no additional package downloads |
| Final pip check | 0 | No broken requirements found |

The final installation/check command was:

```powershell
./venv/Scripts/python.exe -m pip install -r ./ai_engineering/requirements.txt --quiet; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; ./venv/Scripts/python.exe -m pip check
```

The live test starts Uvicorn twice with this subprocess argument list, substituting
the running interpreter and an available local port:

```text
<venv python.exe> -m uvicorn task_api.main:app --host 127.0.0.1 --port <port> --log-level warning
```

It uses a temporary SQLite file through TASK_DB_PATH, sends real HTTP requests,
creates a task, terminates its own server, launches a new server, verifies the
same task persisted, updates/deletes it, and verifies a subsequent 404. Both owned
server processes are cleaned up. The README's interactive `--reload` command was
not separately executed; ordinary Uvicorn startup was verified by this test.

## Runtime recovery and unexpected behavior

The initial sandbox could not execute the venv's configured Python runtime and
reported `No Python` at its existing installation path. Later inspection also
reported access denied. These sandbox observations alone did not establish that
the host installation was absent. Runtime/install/test commands therefore used
approved execution outside the sandbox.

The following download failed inside the sandbox with `Unable to connect to the
remote server` (exit 1), then succeeded with approved network access (exit 0):

```powershell
Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile C:/workspace/.runtime/python-3.11.9-amd64.exe
```

The installer signature was verified as valid, signed by the Python Software
Foundation. The initial installation attempt was:

```powershell
$pythonInstall = Start-Process -FilePath C:/workspace/.runtime/python-3.11.9-amd64.exe -ArgumentList '/quiet InstallAllUsers=0 TargetDir=C:\workspace\.runtime\python311 Include_launcher=0 InstallLauncherAllUsers=0 PrependPath=0 Include_test=0 Include_doc=0 Include_tcltk=0 Shortcuts=0' -WindowStyle Hidden -Wait -PassThru
```

It returned exit 0 but detected an already-registered Python installation and
modified that installation's optional features instead of creating the requested
runtime directory. Consequently this attempted recovery command sequence failed
with exit 1 and was not repeated:

```powershell
C:/workspace/.runtime/python311/python.exe -m venv --upgrade venv; ./venv/Scripts/python.exe --version; ./venv/Scripts/python.exe -m pip install -r ./ai_engineering/requirements.txt
```

A repair operation then returned exit 0:

```powershell
$pythonRepair = Start-Process -FilePath C:/workspace/.runtime/python-3.11.9-amd64.exe -ArgumentList '/repair /quiet' -WindowStyle Hidden -Wait -PassThru
```

The existing venv ran successfully outside the sandbox, so it was reused without
recreation. Finally, the optional components, shortcuts, and PATH setting changed
by the first installer attempt were restored; the restore returned exit 0:

```powershell
$pythonRestore = Start-Process -FilePath C:/workspace/.runtime/python-3.11.9-amd64.exe -ArgumentList '/quiet InstallAllUsers=0 TargetDir=C:\Users\DineshMarre\AppData\Local\Programs\Python\Python311 Include_test=1 Include_doc=1 Include_tcltk=1 Shortcuts=1 PrependPath=1' -WindowStyle Hidden -Wait -PassThru
```

The installer download remains outside the repository in `C:\workspace\.runtime`.

Each pytest run emitted one upstream `StarletteDeprecationWarning`: TestClient's
httpx support is deprecated in favor of httpx2. All tests actually passed. No
warning suppression or extra httpx2 dependency was added.

Review identified an oversized-ID edge case: Python integers beyond SQLite's
64-bit range could overflow SQL parameter binding. Repository guards now return
not-found for these nonexistent IDs; six additional API cases passed.

## Review and changed files

```powershell
git diff --check
git diff -- ai_engineering/requirements.txt
git status --short
git ls-files --others --exclude-standard ai_engineering/4_enhanced_dev_codex
git check-ignore ai_engineering/4_enhanced_dev_codex/data/tasks.db ai_engineering/4_enhanced_dev_codex/task_api/__pycache__/main.cpython-311.pyc ai_engineering/4_enhanced_dev_codex/.pytest_cache/README.md
```

Whitespace review returned exit 0 with no errors. Ignore checks returned exit 0
and confirmed that runtime database files, Python caches, and pytest caches are
ignored. Source review confirmed parameterized SQL, explicit write transactions,
connection cleanup, strict request validation, stable database paths, immutable
server fields, and no logging of environment contents.

Files added under `ai_engineering/4_enhanced_dev_codex`:

- `.gitignore`
- `README.md`
- `VERIFICATION.md`
- `pytest.ini`
- `task_api/__init__.py`
- `task_api/main.py`
- `task_api/schemas.py`
- `task_api/database.py`
- `tests/test_tasks.py`

Updated `ai_engineering/requirements.txt` to record tested API dependencies and
the two required FastAPI transitive packages downloaded during setup. The existing
`.env` was not edited. Tests used temporary databases; the default task database
was not populated.

Unrelated modifications to the earlier assistant exercise and changes involving
the document parsing/chunking exercises were observed and left untouched. No
commit was created.

## Batch launcher verification

Added `run.bat` and updated `SETUP.md` and `README.md`. The launcher finds the
repository root from its own location, reuses a working shared venv or creates/
repairs one with Python 3.11+, installs the shared requirements, and starts Uvicorn
with reload watching limited to this project. Optional arguments are `--check`
for setup only, or a port number. Setup errors stop execution.

Commands executed from the project folder before its rename:

```powershell
cmd.exe /d /c run.bat --check
cmd.exe /d /c run.bat 8017
```

The setup check returned exit 0 and `Setup check passed.` using the existing venv.
The server run completed startup on port 8017. HTTP verification used:

```powershell
$docs = Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8017/docs; Write-Output "GET /docs on 8017: $($docs.StatusCode)"; $schema = Invoke-RestMethod -Uri http://127.0.0.1:8017/openapi.json; Write-Output "API title: $($schema.info.title)"
```

This returned exit 0, `GET /docs on 8017: 200`, and
`API title: Task Management API`. The owned server logged both requests with 200
responses. It was stopped with Ctrl+C and `Y` at the batch termination prompt;
the interrupted shell returned exit 1 with orderly Uvicorn shutdown messages.

An initial default-port attempt also completed startup, but another process was
already listening on port 8000. HTTP responses on that port could not be attributed
to the launcher, so they are not counted as verification. The owned test process
was stopped, and the existing server was left running. No tasks were created,
modified, or deleted during launcher verification.

The project folder was renamed externally to `4_enhanced_dev_codex` during this
work. The guides now use the current folder name; the launcher itself needs no
path changes. An attempted check using the old folder name failed with exit 1
(`The system cannot find the path specified`). The following check from
`C:\workspace` then returned exit 0 and `Setup check passed.`:

```powershell
cmd.exe /d /c C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\4_enhanced_dev_codex\run.bat --check
```

`git diff --check` returned exit 0 with no whitespace errors. Environment-creation
and repair branches were reviewed but not executed in this launcher check because
the shared venv already worked. API tests were not rerun for this launcher and
documentation change; the earlier 64-test result remains the API verification.
