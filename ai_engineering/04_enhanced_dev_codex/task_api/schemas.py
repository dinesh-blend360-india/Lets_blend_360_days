"""Task contracts shared by validation and API documentation."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, StrictStr, StringConstraints
from pydantic import field_validator, model_validator

TaskStatus = Literal["todo", "in_progress", "done"]
Title = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)
]


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: StrictStr | None = None
    status: TaskStatus = "todo"


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: StrictStr | None = None
    status: TaskStatus | None = None

    @field_validator("title", "status")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("Must not be null; omit this field to leave it unchanged")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        return self


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
