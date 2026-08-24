"""fjumcp homework 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="課程作業相關操作。")
console = Console()


@app.command("list")
def list_homework_cmd(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程作業。"""
    from fju_tronclass.services.people import list_homework as _list

    async def _run() -> None:
        async with build_client() as client:
            items = await _list(client, course_id=course_id)

        if as_json:
            emit_json(
                [
                    {
                        "id": h.id,
                        "title": h.title,
                        "type": h.type,
                        "due": h.due,
                        "submitted": h.submitted,
                        "submitted_status": h.submitted_status,
                        "is_closed": h.is_closed,
                        "score": h.score,
                        "group_set_name": h.group_set_name,
                    }
                    for h in items
                ]
            )
            return

        if not items:
            console.print("[dim]這門課沒有作業。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 作業", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("標題", style="bold")
        table.add_column("截止", width=20)
        table.add_column("繳交", width=8)
        table.add_column("成績", width=8)
        for h in items:
            due = h.due.strftime("%Y-%m-%d %H:%M") if h.due else "—"
            submitted = "[green]已繳[/green]" if h.submitted else "[yellow]未繳[/yellow]"
            score = "—" if h.score is None else str(h.score)
            table.add_row(str(h.id), h.title, due, submitted, score)
        console.print(table)
        console.print(f"共 [bold]{len(items)}[/bold] 筆")

    run_async_command(_run())
