"""fjumcp bulletins 子指令。"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="課程公告相關操作。")
console = Console()


@app.command("list")
def list_bulletins(
    course_id: int = typer.Argument(..., help="課程 ID"),
    limit: int = typer.Option(20, "--limit", "-n", help="最多顯示幾筆"),
) -> None:
    """列出指定課程的公告。"""
    from fju_tronclass.services.bulletins import list_bulletins as _list

    async def _run() -> None:
        async with build_client() as client:
            bulletins = await _list(client, course_id=course_id, limit=limit)

        if not bulletins:
            console.print(f"[dim]課程 {course_id} 目前沒有公告。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 公告", show_lines=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("標題", style="bold")
        table.add_column("發布時間", width=20)

        for b in bulletins:
            created = b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "—"
            table.add_row(str(b.id), b.title, created)

        console.print(table)

    asyncio.run(_run())
