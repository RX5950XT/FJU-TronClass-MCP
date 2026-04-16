"""Upload（課程教材）pydantic models。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UploadMeta(BaseModel):
    id: int
    name: str
    size: int = 0
    allow_download: bool = True
    created_at: datetime | None = None


class UploadUrl(BaseModel):
    url: str
