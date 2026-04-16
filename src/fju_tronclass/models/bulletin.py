"""課程公告 pydantic models。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Bulletin(BaseModel):
    id: int
    title: str
    content: str = ""
    course_id: int
    course_name: str = ""
    created_at: datetime | None = None


class BulletinListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Bulletin] = Field(default_factory=list, alias="list")
    total: int = 0
