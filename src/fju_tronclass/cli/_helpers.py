"""CLI 共用工具函式。"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Awaitable

import typer
from rich.console import Console

from fju_tronclass.auth.cookie_store import load_cookie
from fju_tronclass.client.http import TronClassHttp
from fju_tronclass.client.tronclass import TronClassClient
from fju_tronclass.config import get_settings
from fju_tronclass.errors import AuthError, FjuTronclassError, SessionExpiredError

console = Console()


@asynccontextmanager
async def build_client() -> AsyncGenerator[TronClassClient, None]:
    """Context manager：自動讀取 cookie、建立 client，結束後關閉連線。"""
    try:
        cookie = load_cookie()
    except AuthError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None

    settings = get_settings()
    async with TronClassHttp(session_cookie=cookie, base_url=settings.tronclass_base_url) as http:
        yield TronClassClient(http)


def run_async_command(awaitable: Awaitable[None]) -> None:
    """統一執行 async CLI command，將已知錯誤轉為友善訊息。"""
    try:
        asyncio.run(awaitable)
    except SessionExpiredError:
        console.print("[red]Session 已過期，請執行 `fjumcp login` 重新登入。[/red]")
        raise typer.Exit(1) from None
    except FjuTronclassError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None
