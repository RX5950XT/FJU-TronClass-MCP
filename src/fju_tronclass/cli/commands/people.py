"""fjumcp people 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="課程成員相關操作。")
console = Console()


@app.command("list")
def list_people_cmd(
    course_id: int = typer.Argument(..., help="課程 ID"),
    role: str | None = typer.Option(None, "--role", "-r", help="過濾角色：student / instructor / instructor_assistant"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程成員（學生、教師、助教）。"""
    from fju_tronclass.services.people import list_people as _list

    async def _run() -> None:
        async with build_client() as client:
            people = await _list(client, course_id=course_id, role=role)

        if as_json:
            emit_json(
                [
                    {
                        "id": p.id,
                        "name": p.name,
                        "user_no": p.user_no,
                        "role": p.role_label,
                        "roles": p.roles,
                        "group_ids": p.group_ids,
                        "department": p.department,
                        "grade": p.grade,
                    }
                    for p in people
                ]
            )
            return

        if not people:
            console.print("[dim]沒有成員。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 成員", show_lines=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("姓名", style="bold")
        table.add_column("學號", width=12)
        table.add_column("角色", width=8)
        table.add_column("系級")
        for p in people:
            table.add_row(str(p.id), p.name, p.user_no, p.role_label, f"{p.department} {p.grade}".strip())
        console.print(table)
        console.print(f"共 [bold]{len(people)}[/bold] 人")

    run_async_command(_run())
