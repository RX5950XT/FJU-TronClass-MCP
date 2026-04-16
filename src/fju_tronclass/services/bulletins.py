"""課程公告服務。"""

from __future__ import annotations

from fju_tronclass.models.bulletin import Bulletin


async def list_bulletins(client: object, course_id: int, limit: int = 20) -> list[Bulletin]:
    """取得課程公告，最多回傳 limit 筆。"""
    bulletins: list[Bulletin] = await client.get_course_bulletins(course_id)  # type: ignore[attr-defined]
    return bulletins[:limit]
