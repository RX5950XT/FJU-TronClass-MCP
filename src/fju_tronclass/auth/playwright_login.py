"""Playwright 半自動登入：啟動 headed Chromium，讓使用者手動輸入 CAPTCHA 後完成登入。

此模組為選配功能，只有在 `playwright` 套件已安裝時才可使用。
安裝方式：uv add --optional playwright playwright && uv run playwright install chromium
"""

from __future__ import annotations

from fju_tronclass.auth.cookie_store import save_cookie
from fju_tronclass.errors import AuthError
from fju_tronclass.logging import get_logger

logger = get_logger(__name__)

_LOGIN_URL = "https://elearn2.fju.edu.tw/login"
_WAIT_AFTER_LOGIN_MS = 120_000  # 給使用者最多 2 分鐘輸入 CAPTCHA


async def playwright_login(username: str, password: str, base_url: str) -> str:
    """
    使用 Playwright 啟動 headed Chromium，自動填入帳密，讓使用者手動輸入 CAPTCHA。
    成功後擷取 session cookie 並存入 keyring。

    Args:
        username: 輔大學號
        password: 密碼（SSO 帳號密碼）
        base_url: TronClass base URL

    Returns:
        session cookie 值

    Raises:
        AuthError: 若 playwright 未安裝、登入逾時或無法取得 cookie
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise AuthError(
            "Playwright 未安裝。請執行：\n"
            "  uv add --optional playwright playwright\n"
            "  uv run playwright install chromium"
        ) from e

    login_url = f"{base_url}/login"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        logger.info("開啟登入頁面，請在瀏覽器中輸入 CAPTCHA 後按登入")
        await page.goto(login_url)

        # 等待重導至 CAS 登入頁，然後填入帳密
        await page.wait_for_url("**/cas/login**", timeout=10_000)
        await page.fill("input[name=username]", username)
        await page.fill("input[name=password]", password)

        # 等待使用者手動輸入 CAPTCHA 並按提交，最多等 2 分鐘
        logger.info("請在瀏覽器中填入驗證碼並按「登錄」按鈕...")
        await page.wait_for_url(
            f"{base_url}/**",
            timeout=_WAIT_AFTER_LOGIN_MS,
        )

        # 擷取 session cookie
        cookies = await ctx.cookies()
        session_cookie = next(
            (c["value"] for c in cookies if c["name"] == "session"),
            None,
        )
        await browser.close()

    if not session_cookie:
        raise AuthError("登入後無法找到 session cookie，請確認登入是否成功。")

    save_cookie(session_cookie)
    logger.info("Playwright 登入成功，cookie 已儲存")
    return session_cookie
