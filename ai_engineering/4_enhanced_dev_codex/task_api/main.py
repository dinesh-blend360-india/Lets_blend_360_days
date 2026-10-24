"""FastAPI application, configuration, and the five task endpoints."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Annotated

from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException, Path as PathParameter, Response

from .database import TaskDatabase
from .schemas import TaskCreate, TaskResponse, TaskUpdate

PROJECT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_DIR.parent / ".env"
TaskId = Annotated[int, PathParameter(gt=0)]


def database_path() -> Path:
    # Read configuration without loading unrelated secrets into process environment.
    configured = os.environ.get("TASK_DB_PATH")
    if configured is None:
        configured = dotenv_values(ENV_FILE).get("TASK_DB_PATH")
    if not configured:
        return PROJECT_DIR / "data" / "tasks.db"
    path = Path(configured).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_DIR / path).resolve()


def create_app(db_path: str | Path | None = None) -> FastAPI:
    database = TaskDatabase(Path(db_path).resolve() if db_path is not None else database_path())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        yield

    app = FastAPI(
        title="Task Management API",
        description="Local SQLite tasks. Status values: todo, in_progress, done.",
        lifespan=lifespan,
    )

    def require_task(task: dict | None) -> dict:
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.post("/tasks", response_model=TaskResponse, status_code=201)
    def create_task(task: TaskCreate):
        return database.create(task.model_dump())

    @app.get("/tasks", response_model=list[TaskResponse])
    def list_tasks():
        return database.list()

    @app.get("/tasks/{task_id}", response_model=TaskResponse)
    def get_task(task_id: TaskId):
        return require_task(database.get(task_id))

    @app.patch("/tasks/{task_id}", response_model=TaskResponse)
    def update_task(task_id: TaskId, task: TaskUpdate):
        return require_task(database.update(task_id, task.model_dump(exclude_unset=True)))

    @app.delete("/tasks/{task_id}", status_code=204)
    def delete_task(task_id: TaskId):
        if not database.delete(task_id):
            raise HTTPException(status_code=404, detail="Task not found")
        return Response(status_code=204)

    return app


app = create_app()
