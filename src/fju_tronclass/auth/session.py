"""Session 驗證 + cookie 回存的共用路徑。"""

from __future__ import annotations

from fju_tronclass.auth.cookie_store import persist_if_rotated, save_cookie
from fju_tronclass.auth.session_probe import probe_session
from fju_tronclass.client.http import TronClassHttp


async def verify_and_persist(cookie: str, base_url: str, *, always_save: bool = False) -> int:
    """
    探針驗證 session，成功時把 cookie 寫回儲存層。

    always_save=True 用於首次 login（即使伺服器沒 rotate 也要落地）。
    預設只在 rotate 後寫回，避免無謂覆寫。

    Returns:
        課程總數（API `total`）。
    """
    async with TronClassHttp(session_cookie=cookie, base_url=base_url) as http:
        count = await probe_session(http)
        latest = http.session_cookie
        if always_save:
            save_cookie(latest)
        else:
            persist_if_rotated(cookie, latest)
        return count
