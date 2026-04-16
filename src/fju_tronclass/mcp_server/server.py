"""FastMCP server 主程式：註冊所有 TronClass MCP tools。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "fju-tronclass",
    instructions=(
        "輔仁大學 TronClass MCP Server。"
        "可列出課程、待辦事項、公告，下載課程教材，以及標記影片完成度。"
        "使用前請先確認 session cookie 有效（用 fju_check_auth tool 驗證）。"
    ),
)

# 載入所有 tool 模組（透過 import 觸發 @mcp.tool() 裝飾器）
from fju_tronclass.mcp_server.tools import (  # noqa: E402, F401
    auth_tools,
    bulletin_tools,
    course_tools,
    download_tools,
    todo_tools,
    video_tools,
)
