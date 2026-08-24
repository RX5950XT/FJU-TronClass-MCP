"""fjumcp scores / exams。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="成績組成。")
console = Console()


@app.command("list")
def list_scores(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程成績組成與總分是否公布。"""

    async def _run() -> None:
        async with build_client() as client:
            items = await client.get_score_items(course_id)
            total = await client.get_course_score(course_id)
        if as_json:
            emit_json(
                {
                    "published": total.published,
                    "total_score": total.total_score,
                    "bonus": total.bonus,
                    "items": [i.model_dump() for i in items],
                }
            )
            return
        status = "[green]已公布[/green]" if total.published else "[yellow]未公布[/yellow]"
        console.print(f"總分 {total.total_score}　加分 {total.bonus}　{status}")
        table = Table(title=f"課程 {course_id} 成績組成", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("項目")
        table.add_column("%", width=6)
        table.add_column("類型")
        for item in items:
            table.add_row(str(item.id), item.name, str(item.percentage), item.type)
        console.print(table)

    run_async_command(_run())
