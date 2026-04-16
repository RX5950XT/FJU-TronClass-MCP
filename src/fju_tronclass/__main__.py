"""MCP server 進入點：python -m fju_tronclass 或 fju-tronclass-mcp 指令。"""

from __future__ import annotations


def main() -> None:
    from fju_tronclass.config import get_settings
    from fju_tronclass.logging import configure_logging

    settings = get_settings()
    configure_logging(settings.fjumcp_log_level)

    from fju_tronclass.mcp_server.server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
