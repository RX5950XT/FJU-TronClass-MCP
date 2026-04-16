"""課程相關 pydantic models。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Course(BaseModel):
    id: int
    name: str
    code: str = ""
    semester: str = ""
    teacher_name: str = ""
    status: str = "active"
    cover_url: str | None = None


class CourseListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Course] = Field(default_factory=list, alias="list")
    total: int = 0
    page: int = 1
    page_size: int = 20
