"""活動（影片、教材等）pydantic models。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActivityReadRanges(BaseModel):
    completeness: int = 0
    ranges: list[list[int]] = Field(default_factory=list)


class ActivityReadResult(BaseModel):
    completeness: str = ""
    data: ActivityReadRanges = Field(default_factory=ActivityReadRanges)


class Activity(BaseModel):
    id: int
    title: str = ""
    type: str = ""
    duration: int | None = None
    completeness: int = 0
