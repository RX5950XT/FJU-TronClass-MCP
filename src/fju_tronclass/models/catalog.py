"""課程詳情、成績、討論區、個人檔案。"""

from __future__ import annotations

from datetime import datetime
from html import unescape
from re import I, sub

from pydantic import BaseModel, ConfigDict, Field, model_validator


def html_to_text(html: str) -> str:
    text = sub(r"<br\s*/?>", "\n", html or "", flags=I)
    text = sub(r"</p>", "\n", text, flags=I)
    text = sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


class Profile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    user_no: str = ""
    email: str = ""
    department: str = ""
    grade: str = ""
    roles: list[str] = Field(default_factory=list)
    total_course: int = 0

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        dept = data.get("department")
        grade = data.get("grade")
        raw_roles = data.get("roles") or []
        roles: list[str] = []
        if isinstance(raw_roles, list):
            for item in raw_roles:
                if isinstance(item, str):
                    roles.append(item)
                elif isinstance(item, dict):
                    roles.append(str(item.get("name") or item.get("id") or ""))
        return {
            **data,
            "department": dept.get("name", "") if isinstance(dept, dict) else (dept or ""),
            "grade": grade.get("name", "") if isinstance(grade, dict) else (grade or ""),
            "roles": [r for r in roles if r],
        }


class CourseModule(BaseModel):
    id: int
    name: str = ""
    sort: int = 0
    is_hidden: int = 0


class CourseOutline(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int | None = None
    description: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        comment = data.get("comment_chinese")
        desc = ""
        if isinstance(comment, dict):
            desc = comment.get("description") or ""
        return {**data, "description": desc}


class CourseScore(BaseModel):
    id: int | None = None
    total_score: str = "0"
    bonus: str = "0"
    published: bool = False


class ScoreItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    percentage: float = 0
    type: str = ""
    scored: bool = False
    is_announce_score: bool = False
    referrer_id: int | None = None


class ScoreItemListResponse(BaseModel):
    items: list[ScoreItem] = Field(default_factory=list)


class Exam(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    submitted: bool = False


class ExamListResponse(BaseModel):
    items: list[Exam] = Field(default_factory=list, alias="exams")


class ForumTopic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str = ""
    content: str = ""
    like_count: int = 0
    created_at: datetime | None = None
    author: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        created = data.get("created_by")
        author = ""
        if isinstance(created, dict):
            author = created.get("name") or ""
        return {**data, "author": author}


class TopicListResponse(BaseModel):
    items: list[ForumTopic] = Field(default_factory=list, alias="topics")
