"""MCP tools：認證相關。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_check_auth() -> dict:  # type: ignore[type-arg]
    """
    驗證目前的 TronClass session 是否有效。

    回傳：
    - status: "ok" 表示已連線，"error" 表示 session 無效
    - message: 說明訊息
    - course_count: 已連線時的課程數量
    """
    from fju_tronclass.auth.cookie_store import load_cookie
    from fju_tronclass.auth.session_probe import probe_session
    from fju_tronclass.client.http import TronClassHttp
    from fju_tronclass.config import get_settings
    from fju_tronclass.errors import AuthError, SessionExpiredError

    try:
        cookie = load_cookie()
        settings = get_settings()
        async with TronClassHttp(
            session_cookie=cookie, base_url=settings.tronclass_base_url
        ) as http:
            count = await probe_session(http)
        return {
            "status": "ok",
            "message": f"已連線，本學期共 {count} 門課程",
            "course_count": count,
        }
    except (AuthError, SessionExpiredError) as e:
        return {"status": "error", "message": str(e), "course_count": 0}
