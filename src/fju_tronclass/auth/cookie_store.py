"""Session cookie 的儲存與讀取。

優先順序：keyring（Windows Credential Manager）> 環境變數 / .env。
"""

from __future__ import annotations

import keyring

from fju_tronclass.errors import AuthError
from fju_tronclass.logging import get_logger

logger = get_logger(__name__)

_KEYRING_SERVICE = "fju-tronclass-mcp"
_KEYRING_USERNAME = "session"


def load_cookie() -> str:
    """
    讀取 session cookie。
    優先從 keyring 讀取，不存在時從設定（環境變數 / .env）讀取。

    Raises:
        AuthError: 若兩處都找不到 cookie。
    """
    # 1. keyring
    stored = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    if stored:
        logger.debug("從 keyring 讀取 cookie")
        return stored

    # 2. pydantic-settings（環境變數 / .env）
    from fju_tronclass.config import get_settings

    settings = get_settings()
    if settings.tronclass_session_cookie:
        logger.debug("從環境變數讀取 cookie")
        return settings.tronclass_session_cookie

    raise AuthError(
        "找不到 session cookie。\n"
        "請執行以下其中一個指令登入：\n"
        "  fjumcp login              # 互動貼上 cookie\n"
        "  fjumcp login --playwright # 半自動登入（需安裝 playwright）\n"
        "或設定環境變數 TRONCLASS_SESSION_COOKIE。"
    )


def save_cookie(cookie: str) -> None:
    """將 session cookie 存入 keyring（Windows Credential Manager）。"""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, cookie)
    logger.info("Session cookie 已儲存至 keyring")


def delete_cookie() -> None:
    """從 keyring 刪除 session cookie。"""
    try:
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        logger.info("Session cookie 已從 keyring 刪除")
    except keyring.errors.PasswordDeleteError:
        pass
