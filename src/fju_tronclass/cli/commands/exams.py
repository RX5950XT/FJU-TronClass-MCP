"""fjumcp exams。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="考試。")
console = Console()


@app.command("list")
def list_exams(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程考試。"""

    async def _run() -> None:
        async with build_client() as client:
            exams = await client.get_course_exams(course_id)
        if as_json:
            emit_json([e.model_dump() for e in exams])
            return
        if not exams:
            console.print("[dim]這門課沒有考試。[/dim]")
            return
        table = Table(title=f"課程 {course_id} 考試", show_lines=True)
        table.add_column("ID", style="dim")
        table.add_column("標題")
        table.add_column("開始")
        table.add_column("結束")
        table.add_column("繳交")
        for exam in exams:
            start = exam.start_time.strftime("%Y-%m-%d %H:%M") if exam.start_time else "—"
            end = exam.end_time.strftime("%Y-%m-%d %H:%M") if exam.end_time else "—"
            table.add_row(str(exam.id), exam.title, start, end, "已繳" if exam.submitted else "未繳")
        console.print(table)

    run_async_command(_run())
