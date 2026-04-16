"""課程相關服務。"""

from __future__ import annotations

from fju_tronclass.models.course import Course


async def list_courses(client: object, semester: str | None = None) -> list[Course]:
    """取得我的課程清單，可依 semester 過濾。"""
    courses: list[Course] = await client.get_my_courses()  # type: ignore[attr-defined]
    if semester:
        courses = [c for c in courses if c.semester == semester]
    return courses
