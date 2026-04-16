"""待辦事項 pydantic models。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Todo(BaseModel):
    id: int
    title: str
    course_id: int
    course_name: str = ""
    due_time: datetime | None = None
    type: str = "assignment"
    is_done: bool = False


class TodoListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Todo] = Field(default_factory=list, alias="list")
    total: int = 0
