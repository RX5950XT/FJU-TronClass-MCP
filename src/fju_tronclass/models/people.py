"""課程成員、分組、作業的 pydantic models。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Person(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    user_no: str = ""
    roles: list[str] = Field(default_factory=list)
    group_ids: list[int] = Field(default_factory=list)
    department: str = ""
    grade: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        raw_user = data.get("user")
        user = raw_user if isinstance(raw_user, dict) else {}
        dept = data.get("department")
        grade = data.get("grade")
        return {
            **data,
            "id": user.get("id") or data.get("user_id") or data.get("id") or 0,
            "name": data.get("name") or user.get("name") or "",
            "user_no": data.get("user_no") or user.get("user_no") or "",
            "roles": data.get("roles") or [],
            "group_ids": data.get("group_ids") or [],
            "department": dept.get("name", "") if isinstance(dept, dict) else (dept or ""),
            "grade": grade.get("name", "") if isinstance(grade, dict) else (grade or ""),
        }

    @property
    def role_label(self) -> str:
        if "instructor" in self.roles:
            return "教師"
        if "instructor_assistant" in self.roles:
            return "助教"
        if "student" in self.roles:
            return "學生"
        return ",".join(self.roles) or "—"


class PersonListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Person] = Field(default_factory=list)


class GroupMember(BaseModel):
    id: int
    name: str = ""
    user_no: str = ""


class CourseGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    sort: int | None = None
    members: list[GroupMember] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _ignore_numeric_members(cls, data: object) -> object:
        if isinstance(data, dict):
            raw = data.get("members")
            if raw and isinstance(raw[0], int):
                return {**data, "members": []}
        return data


class GroupSet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = ""
    group_count: int = 0
    groups: list[CourseGroup] = Field(default_factory=list)


class GroupSetListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[GroupSet] = Field(default_factory=list, alias="group_sets")


class Homework(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str = ""
    type: str = "homework"
    deadline: datetime | None = None
    end_time: datetime | None = None
    submitted: bool = False
    submitted_status: str = ""
    is_closed: bool = False
    score: float | str | None = None
    group_set_name: str | None = None

    @property
    def due(self) -> datetime | None:
        return self.deadline or self.end_time


class HomeworkListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Homework] = Field(default_factory=list, alias="homework_activities")
    total: int = 0
    page: int = 1
    pages: int = 1
