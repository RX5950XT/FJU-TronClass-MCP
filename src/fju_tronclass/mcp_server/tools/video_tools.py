"""MCP tools：影片完成度。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_mark_video_complete(activity_id: int, duration_seconds: int) -> dict:  # type: ignore[type-arg]
    """
    將指定活動的影片標記為完整觀看。

    此 tool 會呼叫 TronClass API 直接更新觀看進度，
    繞過實際播放驗證。只會增加「完成度」，不會增加「學習時數」。
    使用者須自行評估是否符合課程規範及學業誠信要求。

    參數：
    - activity_id：活動 ID
    - duration_seconds：影片總時長（秒），可從 fju_get_activity 的 duration 欄位取得

    回傳：
    - completeness：最終完成度字串（"full" 表示完整）
    - completeness_pct：完成度百分比（0-100）
    - chunks_sent：總共發送了幾次 API 呼叫
    """
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.video import CHUNK_SIZE, mark_video_complete

    chunks = max(0, -(-duration_seconds // CHUNK_SIZE)) if duration_seconds > 0 else 0

    async with get_client() as client:
        result = await mark_video_complete(client, activity_id=activity_id, duration=duration_seconds)

    if result is None:
        return {"completeness": "none", "completeness_pct": 0, "chunks_sent": 0}

    return {
        "completeness": result.completeness,
        "completeness_pct": result.data.completeness,
        "chunks_sent": chunks,
    }
