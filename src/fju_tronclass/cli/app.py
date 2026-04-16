"""fjumcp CLI 主程式。"""

from __future__ import annotations

import typer

from fju_tronclass.cli.commands import bulletins, courses, download, login, todos, video

app = typer.Typer(
    name="fjumcp",
    help="輔仁大學 TronClass CLI — 管理課程、下載教材、標記影片完成。",
    no_args_is_help=True,
)

app.add_typer(courses.app, name="courses")
app.add_typer(todos.app, name="todos")
app.add_typer(bulletins.app, name="bulletins")
app.add_typer(download.app, name="download")
app.add_typer(video.app, name="video")
app.add_typer(login.app, name="login", invoke_without_command=True)


@app.command("whoami")
def whoami(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="顯示詳細資訊"),  # noqa: B008
) -> None:
    """驗證目前的 session 是否有效，並顯示基本資訊。"""
    import asyncio

    from rich.console import Console

    from fju_tronclass.auth.cookie_store import load_cookie
    from fju_tronclass.auth.session_probe import probe_session
    from fju_tronclass.client.http import TronClassHttp
    from fju_tronclass.config import get_settings
    from fju_tronclass.errors import AuthError, SessionExpiredError

    console = Console()
    settings = get_settings()

    try:
        cookie = load_cookie()
    except AuthError as e:
        console.print(f"[red]認證失敗：{e}[/red]")
        raise typer.Exit(1) from None

    async def _check() -> int:
        async with TronClassHttp(
            session_cookie=cookie, base_url=settings.tronclass_base_url
        ) as http:
            return await probe_session(http)

    try:
        count = asyncio.run(_check())
        console.print(f"[green]已連線[/green] — 本學期共 {count} 門課程")
        if verbose:
            console.print(f"Base URL: {settings.tronclass_base_url}")
    except SessionExpiredError:
        console.print("[red]Session 已過期，請執行 `fjumcp login` 重新登入。[/red]")
        raise typer.Exit(1) from None


@app.command("serve")
def serve() -> None:
    """啟動 MCP server（等同 python -m fju_tronclass）。"""
    from fju_tronclass.__main__ import main

    main()
