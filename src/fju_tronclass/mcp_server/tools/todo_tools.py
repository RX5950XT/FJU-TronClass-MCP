"""MCP tools：待辦事項。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_list_todos(include_done: bool = False) -> list[dict]:  # type: ignore[type-arg]
    """
    列出 TronClass 的待辦事項。

    參數：
    - include_done：是否包含已完成的項目（預設 false，只回傳未完成）

    回傳列表，每筆包含：id、title、course_id、course_name、
    due_time（截止時間，ISO 8601）、type（assignment / video 等）、is_done
    """
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.todos import list_todos

    async with get_client() as client:
        todos = await list_todos(client, include_done=include_done)

    return [t.model_dump(mode="json") for t in todos]
