"""fjumcp CLI 主程式。"""

from __future__ import annotations

import typer

from fju_tronclass.cli.commands import activities, bulletins, courses, download, login, todos, video

app = typer.Typer(
    name="fjumcp",
    help="輔仁大學 TronClass CLI — 管理課程、下載教材、標記影片完成。",
    no_args_is_help=True,
)

app.add_typer(courses.app, name="courses")
app.add_typer(todos.app, name="todos")
app.add_typer(bulletins.app, name="bulletins")
app.add_typer(activities.app, name="activities")
app.add_typer(download.app, name="download")
app.add_typer(video.app, name="video")
app.add_typer(login.app, name="login", invoke_without_command=True)


@app.callback()
def _init_logging() -> None:
    from fju_tronclass.config import get_settings
    from fju_tronclass.logging import configure_logging

    configure_logging(get_settings().fjumcp_log_level)


def _run_session_probe(*, quiet: bool, verbose: bool) -> None:
    """whoami / keepalive 共用：驗證 session 並回存 rotate 後的 cookie。"""
    import asyncio

    from rich.console import Console

    from fju_tronclass.auth.cookie_store import load_cookie, parse_cookie_expiry
    from fju_tronclass.auth.session import verify_and_persist
    from fju_tronclass.config import get_settings
    from fju_tronclass.errors import AuthError, ServerError, SessionExpiredError

    console = Console(stderr=quiet)
    settings = get_settings()

    try:
        cookie = load_cookie()
    except AuthError as e:
        console.print(f"[red]認證失敗：{e}[/red]")
        raise typer.Exit(1) from None

    try:
        count = asyncio.run(verify_and_persist(cookie, settings.tronclass_base_url))
    except SessionExpiredError:
        console.print("[red]Session 已過期，請執行 `fjumcp login` 重新登入。[/red]")
        raise typer.Exit(1) from None
    except ServerError as e:
        console.print(f"[red]連線失敗：{e}[/red]")
        raise typer.Exit(1) from None

    if quiet:
        return

    expiry = parse_cookie_expiry(load_cookie())
    console.print(f"[green]已連線[/green] — 本學期共 {count} 門課程")
    if verbose:
        console.print(f"Base URL: {settings.tronclass_base_url}")
        if expiry is not None:
            console.print(f"Cookie 到期（UTC）：{expiry.isoformat()}")


@app.command("whoami")
def whoami(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="顯示詳細資訊"),  # noqa: B008
    quiet: bool = typer.Option(False, "--quiet", "-q", help="成功時不輸出（排程用）"),  # noqa: B008
) -> None:
    """驗證目前的 session 是否有效，並把 rotate 後的 cookie 寫回。"""
    _run_session_probe(quiet=quiet, verbose=verbose)


@app.command("keepalive")
def keepalive(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="顯示課程數與到期時間"),  # noqa: B008
) -> None:
    """輕量 ping，滑動延長 24h session。成功預設安靜，失敗才輸出。"""
    _run_session_probe(quiet=not verbose, verbose=verbose)


@app.command("serve")
def serve() -> None:
    """啟動 MCP server（等同 python -m fju_tronclass）。"""
    from fju_tronclass.__main__ import main

    main()
