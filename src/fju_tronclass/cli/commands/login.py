"""fjumcp login 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer(help="管理登入 / Cookie 設定。", no_args_is_help=True)
console = Console()


@app.callback(invoke_without_command=True)
def login_default(ctx: typer.Context) -> None:
    """互動式貼上 session cookie（預設登入方式）。"""
    if ctx.invoked_subcommand is None:
        _cookie_login()


@app.command("cookie")
def cookie_login() -> None:
    """互動式貼上 session cookie。"""
    _cookie_login()


def _cookie_login() -> None:
    import asyncio

    from fju_tronclass.auth.cookie_store import save_cookie
    from fju_tronclass.auth.session_probe import probe_session
    from fju_tronclass.client.http import TronClassHttp
    from fju_tronclass.config import get_settings
    from fju_tronclass.errors import SessionExpiredError

    console.print("[bold]輔大 TronClass — Cookie 登入[/bold]")
    console.print("1. 在瀏覽器登入 https://elearn2.fju.edu.tw/")
    console.print("2. 開啟 DevTools（F12）→ Application → Cookies → elearn2.fju.edu.tw")
    console.print("3. 複製 [bold]session[/bold] 欄位的值（以 V2- 開頭）")

    cookie = Prompt.ask("\n請貼上 session cookie 值")
    cookie = cookie.strip()

    if not cookie:
        console.print("[red]Cookie 不可為空。[/red]")
        raise typer.Exit(1)

    settings = get_settings()

    async def _verify() -> int:
        async with TronClassHttp(
            session_cookie=cookie, base_url=settings.tronclass_base_url
        ) as http:
            return await probe_session(http)

    try:
        count = asyncio.run(_verify())
        save_cookie(cookie)
        console.print(f"[green]登入成功！[/green] 本學期共 {count} 門課程。")
        console.print("Cookie 已儲存至 Windows Credential Manager。")
    except SessionExpiredError:
        console.print("[red]Cookie 無效或已過期，請重新複製。[/red]")
        raise typer.Exit(1) from None


def playwright_login_cmd(
    username: str = typer.Option(..., "--username", "-u", prompt="學號", help="輔大學號"),
    password: str = typer.Option(
        ..., "--password", "-p", prompt="密碼", hide_input=True, help="密碼"
    ),
) -> None:
    """Playwright 半自動登入（需安裝 playwright）。"""
    import asyncio

    from fju_tronclass.auth.playwright_login import playwright_login
    from fju_tronclass.config import get_settings
    from fju_tronclass.errors import AuthError

    settings = get_settings()

    console.print("[bold]Playwright 半自動登入[/bold]")
    console.print("瀏覽器即將開啟，請在 CAPTCHA 輸入後按「登錄」…")

    try:
        asyncio.run(playwright_login(username, password, settings.tronclass_base_url))
        console.print("[green]登入成功！Cookie 已儲存。[/green]")
    except AuthError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None


@app.command("logout")
def logout() -> None:
    """刪除已儲存的 session cookie。"""
    from fju_tronclass.auth.cookie_store import delete_cookie

    delete_cookie()
    console.print("已登出，session cookie 已從 Credential Manager 移除。")
