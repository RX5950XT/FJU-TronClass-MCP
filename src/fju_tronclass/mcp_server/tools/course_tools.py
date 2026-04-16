"""MCP tools：課程相關。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_list_courses(semester: str | None = None) -> list[dict]:  # type: ignore[type-arg]
    """
    列出我的輔大 TronClass 課程清單。

    參數：
    - semester（可選）：學期代碼，例如 "113-2"，不填則回傳所有學期課程

    回傳課程列表，每筆包含：id、name（課程名稱）、code（課程代碼）、
    semester（學期）、teacher_name（授課教師）、status（active / inactive）
    """
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.courses import list_courses

    async with get_client() as client:
        courses = await list_courses(client, semester=semester)

    return [c.model_dump() for c in courses]


@mcp.tool()
async def fju_get_activity(course_id: int, activity_id: int) -> dict:  # type: ignore[type-arg]
    """
    取得指定課程中某個學習活動的詳情。

    參數：
    - course_id：課程 ID（從 fju_list_courses 取得）
    - activity_id：活動 ID

    回傳活動詳情：id、title、type、duration（影片時長，秒）、completeness（完成度 0-100）
    """
    from fju_tronclass.mcp_server._client_factory import get_client

    async with get_client() as client:
        activity = await client.get_learning_activity(course_id, activity_id)

    return activity.model_dump()
