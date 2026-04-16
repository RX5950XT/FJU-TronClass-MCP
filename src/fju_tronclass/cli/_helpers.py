"""CLI 共用工具函式。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fju_tronclass.auth.cookie_store import load_cookie
from fju_tronclass.client.http import TronClassHttp
from fju_tronclass.client.tronclass import TronClassClient
from fju_tronclass.config import get_settings
from fju_tronclass.errors import AuthError
from rich.console import Console
import typer

console = Console()


@asynccontextmanager
async def build_client() -> AsyncGenerator[TronClassClient, None]:
    """Context manager：自動讀取 cookie、建立 client，結束後關閉連線。"""
    try:
        cookie = load_cookie()
    except AuthError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    settings = get_settings()
    async with TronClassHttp(session_cookie=cookie, base_url=settings.tronclass_base_url) as http:
        yield TronClassClient(http)
