from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from fastapi.testclient import TestClient
import httpx
import pytest

from task_api import main
from task_api.main import create_app

PROJECT_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "tasks.db")) as client:
        yield client


def test_crud_and_defaults(client):
    assert client.get("/tasks").json() == []
    before = datetime.now(timezone.utc)
    response = client.post("/tasks", json={"title": "  First task  "})
    assert response.status_code == 201
    first = response.json()
    assert first["title"] == "First task"
    assert first["description"] is None
    assert first["status"] == "todo"
    assert isinstance(first["id"], int) and first["id"] > 0
    created_at = datetime.fromisoformat(first["created_at"].replace("Z", "+00:00"))
    assert created_at.utcoffset().total_seconds() == 0
    assert before <= created_at <= datetime.now(timezone.utc)

    second_response = client.post("/tasks", json={"title": "Second", "description": "Details"})
    assert second_response.status_code == 201
    second = second_response.json()
    assert second["id"] > first["id"]
    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert listed.json() == [first, second]
    retrieved = client.get(f"/tasks/{first['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == first

    updated = client.patch(f"/tasks/{second['id']}", json={"status": "done"})
    assert updated.status_code == 200
    expected = {**second, "status": "done"}
    assert updated.json() == expected
    renamed = client.patch(f"/tasks/{second['id']}", json={"title": " Renamed "})
    assert renamed.status_code == 200
    expected["title"] = "Renamed"
    assert renamed.json() == expected
    cleared = client.patch(f"/tasks/{second['id']}", json={"description": None})
    assert cleared.status_code == 200
    expected["description"] = None
    assert cleared.json() == expected

    deleted = client.delete(f"/tasks/{second['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/tasks/{second['id']}").status_code == 404
    assert client.get("/tasks").json() == [first]


@pytest.mark.parametrize("status", ["todo", "in_progress", "done"])
def test_allowed_statuses(client, status):
    response = client.post("/tasks", json={"title": "Status", "status": status})
    assert response.status_code == 201
    assert response.json()["status"] == status
    task_id = response.json()["id"]
    for next_status in ["done", "todo", "in_progress"]:
        updated = client.patch(f"/tasks/{task_id}", json={"status": next_status})
        assert updated.status_code == 200
        assert updated.json()["status"] == next_status


@pytest.mark.parametrize("field, value", [
    ("title", ""), ("title", " \t\n "), ("title", None),
    ("title", 123), ("title", False), ("title", []),
    ("status", "invalid"), ("status", "DONE"), ("status", " done "),
    ("status", None), ("status", 1), ("description", 42),
    ("id", 100), ("created_at", "2020-01-01T00:00:00Z"), ("unknown", "value"),
])
@pytest.mark.parametrize("method", ["post", "patch"])
def test_field_validation_has_no_side_effects(client, field, value, method):
    original = client.post("/tasks", json={"title": "Original"}).json()
    payload = {"title": "New", field: value} if method == "post" else {field: value}
    url = "/tasks" if method == "post" else f"/tasks/{original['id']}"
    response = getattr(client, method)(url, json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", field] and error["msg"] for error in errors)
    assert client.get("/tasks").json() == [original]


def test_missing_title_and_empty_patch(client):
    missing = client.post("/tasks", json={})
    assert missing.status_code == 422
    assert missing.json()["detail"][0]["loc"] == ["body", "title"]
    task = client.post("/tasks", json={"title": "Unchanged"}).json()
    response = client.patch(f"/tasks/{task['id']}", json={})
    assert response.status_code == 422
    assert "at least one field" in response.json()["detail"][0]["msg"]
    assert client.get(f"/tasks/{task['id']}").json() == task


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
@pytest.mark.parametrize("task_id", [999, 2**63, 10**30])
def test_not_found(client, method, task_id):
    kwargs = {"json": {"title": "Missing"}} if method == "patch" else {}
    response = getattr(client, method)(f"/tasks/{task_id}", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


@pytest.mark.parametrize("task_id", ["0", "-1", "abc", "1.5"])
@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_invalid_path_ids(client, method, task_id):
    kwargs = {"json": {"title": "Valid"}} if method == "patch" else {}
    response = getattr(client, method)(f"/tasks/{task_id}", **kwargs)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "task_id"]


@pytest.mark.parametrize("method, url", [("post", "/tasks"), ("patch", "/tasks/1")])
def test_malformed_and_missing_body(client, method, url):
    response = getattr(client, method)(url, content="{", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert getattr(client, method)(url).status_code == 422


def test_description_update_and_sql_parameterization(client):
    title = "Robert'); DROP TABLE tasks;--"
    created = client.post("/tasks", json={"title": title, "description": ""})
    assert created.status_code == 201
    task = created.json()
    response = client.patch(f"/tasks/{task['id']}", json={"description": "Updated details"})
    assert response.status_code == 200
    assert response.json() == {**task, "description": "Updated details"}
    assert len(client.get("/tasks").json()) == 1


def test_persistence_across_app_instances(tmp_path):
    path = tmp_path / "nested" / "tasks.db"
    with TestClient(create_app(path)) as first:
        task = first.post("/tasks", json={"title": "Persistent"}).json()
    assert path.is_file()
    with TestClient(create_app(path)) as restarted:
        assert restarted.get(f"/tasks/{task['id']}").json() == task
        assert restarted.get("/tasks").json() == [task]
        next_task = restarted.post("/tasks", json={"title": "Next"}).json()
        assert next_task["id"] > task["id"]


def test_persistence_across_processes(tmp_path):
    script = """
import json, sys
from fastapi.testclient import TestClient
from task_api.main import create_app
with TestClient(create_app(sys.argv[1])) as client:
    if sys.argv[2] == 'create':
        response = client.post('/tasks', json={'title': 'Process persistence'})
        assert response.status_code == 201
    else:
        response = client.get('/tasks/1')
        assert response.status_code == 200
    print(json.dumps(response.json()))
"""
    path = tmp_path / "processes.db"
    results = []
    for action in ("create", "read"):
        result = subprocess.run(
            [sys.executable, "-c", script, str(path), action], cwd=PROJECT_DIR,
            capture_output=True, text=True, timeout=30, check=True,
        )
        results.append(json.loads(result.stdout))
    assert results[0] == results[1]


def test_live_uvicorn_restart(tmp_path):
    """Exercise real TCP requests and a server restart against the same file."""
    environment = {**os.environ, "TASK_DB_PATH": str(tmp_path / "live.db")}
    task = None
    for restart in (False, True):
        with socket.socket() as available_port:
            available_port.bind(("127.0.0.1", 0))
            port = available_port.getsockname()[1]
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "task_api.main:app", "--host", "127.0.0.1",
             "--port", str(port), "--log-level", "warning"],
            cwd=PROJECT_DIR, env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=2) as live:
                deadline = time.monotonic() + 20
                while True:
                    if process.poll() is not None:
                        pytest.fail(f"Uvicorn exited before startup: {process.communicate()[1]}")
                    try:
                        ready = live.get("/tasks")
                        assert ready.status_code == 200
                        break
                    except httpx.TransportError:
                        if time.monotonic() >= deadline:
                            pytest.fail("Uvicorn did not start within 20 seconds")
                        time.sleep(0.1)
                if not restart:
                    response = live.post("/tasks", json={"title": "Real server"})
                    assert response.status_code == 201
                    task = response.json()
                else:
                    assert ready.json() == [task]
                    assert live.get(f"/tasks/{task['id']}").json() == task
                    assert live.patch(f"/tasks/{task['id']}", json={"status": "done"}).status_code == 200
                    assert live.delete(f"/tasks/{task['id']}").status_code == 204
                    assert live.get(f"/tasks/{task['id']}").status_code == 404
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5)


def test_database_configuration(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("TASK_DB_PATH=dotenv/tasks.db\n", encoding="utf-8")
    monkeypatch.setattr(main, "ENV_FILE", env_file)
    monkeypatch.delenv("TASK_DB_PATH", raising=False)
    assert main.database_path() == (PROJECT_DIR / "dotenv/tasks.db").resolve()
    monkeypatch.setenv("TASK_DB_PATH", str(tmp_path / "override.db"))
    assert main.database_path() == tmp_path / "override.db"
    monkeypatch.delenv("TASK_DB_PATH")
    env_file.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main.database_path() == PROJECT_DIR / "data/tasks.db"


def test_openapi_documents_statuses(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert schemas["TaskCreate"]["properties"]["status"]["enum"] == ["todo", "in_progress", "done"]
