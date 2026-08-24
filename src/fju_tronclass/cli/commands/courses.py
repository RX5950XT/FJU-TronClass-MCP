"""fjumcp courses 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command

app = typer.Typer(help="課程相關操作。")
console = Console()


@app.command("list")
def list_courses(
    semester: str | None = typer.Option(None, "--semester", "-s", help="過濾學期（例：113-2）"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出我的課程清單。"""
    from fju_tronclass.cli._output import emit_json
    from fju_tronclass.services.courses import list_courses as _list

    async def _run() -> None:
        async with build_client() as client:
            courses = await _list(client, semester=semester)

        if as_json:
            emit_json(
                [
                    {
                        "id": c.id,
                        "name": c.name,
                        "code": c.code,
                        "semester": c.semester,
                        "teacher_name": c.teacher_name,
                    }
                    for c in courses
                ]
            )
            return

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

    run_async_command(_run())


@app.command("show")
def show_course(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示課程詳情。"""
    from fju_tronclass.cli._output import emit_json
    from fju_tronclass.models.catalog import html_to_text

    async def _run() -> None:
        async with build_client() as client:
            data = await client.get_course(course_id)
        if as_json:
            emit_json(data)
            return
        instructors = data.get("instructors") or []
        names = "、".join(
            (i.get("name") or "") for i in instructors if isinstance(i, dict)
        )
        sem = data.get("semester")
        if not isinstance(sem, dict):
            sem = {}
        year = data.get("academic_year")
        if not isinstance(year, dict):
            year = {}
        console.print(f"[bold]{data.get('name')}[/bold]  #{data.get('id')}")
        console.print(f"代碼 {data.get('course_code')}　學分 {data.get('credit')}　教師 {names}")
        console.print(f"學期 {year.get('name', '')}-{sem.get('real_name') or sem.get('name', '')}")
        console.print(f"期間 {data.get('start_date')} ～ {data.get('end_date')}")
        outline = data.get("course_outline")
        if not isinstance(outline, dict):
            outline = {}
        comment = outline.get("comment_chinese")
        if not isinstance(comment, dict):
            comment = {}
        text = html_to_text(str(comment.get("description") or ""))
        if text:
            console.print("\n" + text[:1200])

    run_async_command(_run())


@app.command("outline")
def show_outline(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示課程大綱。"""
    from fju_tronclass.cli._output import emit_json
    from fju_tronclass.models.catalog import html_to_text

    async def _run() -> None:
        async with build_client() as client:
            outline = await client.get_course_outline(course_id)
        if as_json:
            emit_json(outline.model_dump())
            return
        console.print(html_to_text(outline.description) or "[dim]沒有大綱。[/dim]")

    run_async_command(_run())


@app.command("modules")
def list_modules(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程週次／模組。"""
    from fju_tronclass.cli._output import emit_json

    async def _run() -> None:
        async with build_client() as client:
            modules = await client.get_course_modules(course_id)
        if as_json:
            emit_json([m.model_dump() for m in modules])
            return
        table = Table(title=f"課程 {course_id} 模組")
        table.add_column("ID", style="dim")
        table.add_column("名稱")
        for module in modules:
            table.add_row(str(module.id), module.name)
        console.print(table)

    run_async_command(_run())
