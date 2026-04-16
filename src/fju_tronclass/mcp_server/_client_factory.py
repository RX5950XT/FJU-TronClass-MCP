"""MCP tool 共用：建立 TronClassClient 實例。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fju_tronclass.auth.cookie_store import load_cookie
from fju_tronclass.client.http import TronClassHttp
from fju_tronclass.client.tronclass import TronClassClient
from fju_tronclass.config import get_settings


@asynccontextmanager
async def get_client() -> AsyncGenerator[TronClassClient, None]:
    """Context manager：建立並回傳 TronClassClient。"""
    cookie = load_cookie()
    settings = get_settings()
    async with TronClassHttp(session_cookie=cookie, base_url=settings.tronclass_base_url) as http:
        yield TronClassClient(http)
