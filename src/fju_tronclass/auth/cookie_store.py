"""Session cookie 的儲存與讀取。

優先順序：keyring > 本機檔案（XDG）> 環境變數 / .env。

Windows 走 Credential Manager；Linux / WSL / headless 沒有可用 keyring 時，
改寫到 ~/.config/fju-tronclass/session（權限 0600），rotation 才不會丟。
"""

from __future__ import annotations

import os
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

import keyring

from fju_tronclass.errors import AuthError
from fju_tronclass.logging import get_logger

logger = get_logger(__name__)

_KEYRING_SERVICE = "fju-tronclass-mcp"
_KEYRING_USERNAME = "session"


def cookie_file_path() -> Path:
    """XDG config 下的 cookie 檔路徑。"""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "fju-tronclass" / "session"


def parse_cookie_expiry(cookie: str) -> datetime | None:
    """從 V2 cookie 第三段解析到期時間（epoch ms）。解析失敗回 None。"""
    parts = cookie.strip().split(".")
    if len(parts) < 3 or not parts[2].isdigit():
        return None
    try:
        return datetime.fromtimestamp(int(parts[2]) / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError):
        return None


def persist_if_rotated(original: str, current: str) -> bool:
    """cookie 有變才寫回。回傳是否有寫入。"""
    if current and current != original:
        save_cookie(current)
        return True
    return False


def _read_file() -> str | None:
    path = cookie_file_path()
    try:
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
            return value or None
    except OSError as exc:
        logger.debug("讀取 cookie 檔失敗", path=str(path), error=str(exc))
    return None


def _write_file(cookie: str) -> None:
    path = cookie_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cookie, encoding="utf-8")
    with suppress(OSError):
        # Windows 上 chmod 可能無效，忽略即可
        path.chmod(0o600)


def _delete_file() -> None:
    path = cookie_file_path()
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.debug("刪除 cookie 檔失敗", path=str(path), error=str(exc))


def _keyring_get() -> str | None:
    try:
        stored = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception as exc:  # noqa: BLE001 — keyring backend 在 WSL 常直接炸
        logger.debug("keyring 讀取失敗，改走檔案 / 環境變數", error=str(exc))
        return None
    return stored or None


def _keyring_set(cookie: str) -> bool:
    try:
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, cookie)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("keyring 寫入失敗，改走檔案", error=str(exc))
        return False


def _keyring_delete() -> None:
    with suppress(Exception):  # noqa: BLE001
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)


def load_cookie() -> str:
    """
    讀取 session cookie。
    優先 keyring，其次本機檔案，最後環境變數 / .env。

    Raises:
        AuthError: 若三處都找不到 cookie。
    """
    stored = _keyring_get()
    if stored:
        logger.debug("從 keyring 讀取 cookie")
        return stored

    stored = _read_file()
    if stored:
        logger.debug("從本機檔案讀取 cookie", path=str(cookie_file_path()))
        return stored

    from fju_tronclass.config import get_settings

    settings = get_settings()
    if settings.tronclass_session_cookie:
        logger.debug("從環境變數讀取 cookie")
        return settings.tronclass_session_cookie

    raise AuthError(
        "找不到 session cookie。\n"
        "請執行以下其中一個指令登入：\n"
        "  fjumcp login --cookie 'V2-...'\n"
        "  fjumcp login              # 互動貼上 cookie\n"
        "或設定環境變數 TRONCLASS_SESSION_COOKIE。"
    )


def save_cookie(cookie: str) -> None:
    """將 session cookie 寫入 keyring（若可用）與本機檔案。"""
    cookie = cookie.strip()
    keyring_ok = _keyring_set(cookie)
    _write_file(cookie)
    if keyring_ok:
        logger.debug("Session cookie 已儲存至 keyring 與本機檔案")
    else:
        logger.debug("Session cookie 已儲存至本機檔案", path=str(cookie_file_path()))


def delete_cookie() -> None:
    """從 keyring 與本機檔案刪除 session cookie。"""
    _keyring_delete()
    _delete_file()
    logger.info("Session cookie 已刪除")
