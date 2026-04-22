"""課程相關 pydantic models。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Course(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    code: str = ""
    semester: str = ""
    teacher_name: str = ""
    status: str = "active"
    cover_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_api_response(cls, data: object) -> object:
        """將 API 巢狀物件轉為扁平欄位，同時保持直接建構相容性。"""
        if not isinstance(data, dict):
            return data

        # semester: {"name": "1142", "real_name": "2"} → "114-2"
        sem = data.get("semester")
        if isinstance(sem, dict):
            ay = data.get("academic_year", {})
            ay_name = ay.get("name", "") if isinstance(ay, dict) else ""
            real_name = sem.get("real_name", "")
            data = {
                **data,
                "semester": f"{ay_name}-{real_name}" if ay_name and real_name else sem.get("name", ""),
            }

        # instructors: [{"name": "吳至原"}] → teacher_name
        if "teacher_name" not in data or not data["teacher_name"]:
            instructors = data.get("instructors", [])
            if instructors and isinstance(instructors[0], dict):
                data = {**data, "teacher_name": instructors[0].get("name", "")}

        # course_code → code
        if not data.get("code") and data.get("course_code"):
            data = {**data, "code": data["course_code"]}

        return data


class CourseListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[Course] = Field(default_factory=list, alias="courses")
    total: int = 0
    page: int = 1
    page_size: int = 20
