"""fjumcp todos 子指令。"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="待辦事項相關操作。")
console = Console()


@app.command("list")
def list_todos(
    include_done: bool = typer.Option(False, "--include-done", help="包含已完成項目"),
) -> None:
    """列出待辦事項。"""
    from fju_tronclass.services.todos import list_todos as _list

    async def _run() -> None:
        async with build_client() as client:
            todos = await _list(client, include_done=include_done)

        if not todos:
            console.print("[green]目前沒有待辦事項！[/green]")
            return

        table = Table(title="待辦事項", show_lines=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("標題", style="bold")
        table.add_column("課程")
        table.add_column("截止時間", width=20)
        table.add_column("類型", width=10)
        table.add_column("狀態", width=8)

        for t in todos:
            due = t.due_time.strftime("%Y-%m-%d %H:%M") if t.due_time else "—"
            status = "[green]已完成[/green]" if t.is_done else "[yellow]待完成[/yellow]"
            table.add_row(str(t.id), t.title, t.course_name, due, t.type, status)

        console.print(table)
        console.print(f"共 [bold]{len(todos)}[/bold] 筆")

    asyncio.run(_run())
