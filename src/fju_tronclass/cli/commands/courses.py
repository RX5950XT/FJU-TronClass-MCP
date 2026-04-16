"""fjumcp courses 子指令。"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="課程相關操作。")
console = Console()


@app.command("list")
def list_courses(
    semester: str | None = typer.Option(None, "--semester", "-s", help="過濾學期（例：113-2）"),
) -> None:
    """列出我的課程清單。"""
    from fju_tronclass.services.courses import list_courses as _list

    async def _run() -> None:
        async with build_client() as client:
            courses = await _list(client, semester=semester)

        table = Table(title="我的課程", show_lines=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("課程名稱", style="bold")
        table.add_column("代碼", width=10)
        table.add_column("學期", width=8)
        table.add_column("授課教師")

        for c in courses:
            table.add_row(str(c.id), c.name, c.code, c.semester, c.teacher_name)

        console.print(table)
        console.print(f"共 [bold]{len(courses)}[/bold] 門課程")

    asyncio.run(_run())
