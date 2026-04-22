"""活動（影片、教材等）pydantic models。

從 tronclass-video-player 與 tronclass-downloader 技能的逆向成果整理：
- type="material"：教材，有 uploads 欄位
- type="online_video"：影片，有 data.duration 與 completenessTip 欄位
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActivityData(BaseModel):
    """活動附帶資料（影片使用）。"""

    duration: int | None = None  # 影片總時長（秒）


class ActivityUpload(BaseModel):
    """活動中的教材附件。"""

    id: int
    name: str = ""
    size: int = 0


class ActivityReadRanges(BaseModel):
    completeness: int = 0
    ranges: list[list[int]] = Field(default_factory=list)


class ActivityReadResult(BaseModel):
    completeness: str = ""
    data: ActivityReadRanges = Field(default_factory=ActivityReadRanges)


class Activity(BaseModel):
    """課程活動（教材或影片）。

    - type="material"：教材，有 uploads[] 附件清單
    - type="online_video"：影片，有 data.duration 與 completeness_tip
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str | None = None  # 教材類型使用 name 欄位（可為 null）
    title: str = ""           # 影片/活動標題
    type: str = ""
    completeness: int | None = None
    completeness_tip: str | None = Field(default=None, alias="completenessTip")
    uploads: list[ActivityUpload] = Field(default_factory=list)
    data: ActivityData | None = None

    @property
    def display_name(self) -> str:
        """回傳最佳顯示名稱（title 優先，次為 name）。"""
        return self.title or (self.name or "")

    @property
    def video_duration(self) -> int | None:
        """影片時長（秒）；非影片類型回傳 None。"""
        if self.data and self.data.duration:
            return self.data.duration
        return None

    @property
    def is_video(self) -> bool:
        return self.type == "online_video"

    @property
    def is_material(self) -> bool:
        return self.type == "material"

    @property
    def is_complete(self) -> bool:
        """根據 completenessTip 或 completeness 欄位判斷是否已完成。"""
        if self.completeness_tip:
            return "已完成" in self.completeness_tip
        return (self.completeness or 0) >= 100


class ActivityListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Activity] = Field(default_factory=list, alias="activities")
    total: int = 0
