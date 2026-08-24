"""fjumcp profile。"""

from __future__ import annotations

import typer
from rich.console import Console

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="目前登入者資料。")
console = Console()


@app.callback(invoke_without_command=True)
def profile_default(
    ctx: typer.Context,
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示目前登入者。"""
    if ctx.invoked_subcommand is not None:
        return

    async def _run() -> None:
        async with build_client() as client:
            profile = await client.get_profile()
        payload = {
            "id": profile.id,
            "name": profile.name,
            "user_no": profile.user_no,
            "email": profile.email,
            "department": profile.department,
            "grade": profile.grade,
            "roles": profile.roles,
            "total_course": profile.total_course,
        }
        if as_json:
            emit_json(payload)
            return
        console.print(f"[bold]{profile.name}[/bold]  {profile.user_no}")
        console.print(f"{profile.department} {profile.grade}".strip())
        console.print(f"email: {profile.email}")
        console.print(f"roles: {', '.join(profile.roles) or '—'}")
        console.print(f"課程數：{profile.total_course}")

    run_async_command(_run())
