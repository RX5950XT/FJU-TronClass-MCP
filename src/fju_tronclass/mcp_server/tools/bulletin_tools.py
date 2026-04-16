"""MCP tools：課程公告。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_list_course_bulletins(course_id: int, limit: int = 20) -> list[dict]:  # type: ignore[type-arg]
    """
    取得指定課程的公告列表。

    參數：
    - course_id：課程 ID（從 fju_list_courses 取得）
    - limit：最多回傳幾筆（預設 20）

    回傳列表，每筆包含：id、title、content（公告內容）、
    course_id、course_name、created_at（ISO 8601）
    """
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.bulletins import list_bulletins

    async with get_client() as client:
        bulletins = await list_bulletins(client, course_id=course_id, limit=limit)

    return [b.model_dump(mode="json") for b in bulletins]
