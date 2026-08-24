"""fjumcp digest — 一次看待辦與本學期課表。"""

from __future__ import annotations

import typer
from rich.console import Console

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="待辦 + 本學期課表摘要。")
console = Console()


@app.callback(invoke_without_command=True)
def digest_default(
    ctx: typer.Context,
    semester: str | None = typer.Option(None, "--semester", "-s", help="學期，預設最新有課的學期"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示登入者、未完成待辦、指定學期課程。"""
    if ctx.invoked_subcommand is not None:
        return
    from fju_tronclass.services.courses import list_courses
    from fju_tronclass.services.todos import list_todos

    async def _run() -> None:
        async with build_client() as client:
            profile = await client.get_profile()
            todos = await list_todos(client, include_done=False)
            courses = await list_courses(client, semester=semester)
        picked = semester
        if picked is None and courses:
            latest = max((c.semester for c in courses if c.semester), default="")
            if latest:
                courses = [c for c in courses if c.semester == latest]
                picked = latest
        payload = {
            "profile": {"name": profile.name, "user_no": profile.user_no, "department": profile.department},
            "semester": picked,
            "todos": [
                {
                    "id": t.id,
                    "title": t.title,
                    "course_name": t.course_name,
                    "due_time": t.due_time,
                    "type": t.type,
                }
                for t in todos
            ],
            "courses": [{"id": c.id, "name": c.name, "teacher_name": c.teacher_name} for c in courses],
        }
        if as_json:
            emit_json(payload)
            return
        console.print(f"[bold]{profile.name}[/bold]  {profile.department} {profile.grade}".strip())
        console.print(f"學期 {picked or '全部'}　待辦 {len(todos)}　課程 {len(courses)}")
        if todos:
            console.print("\n[bold]未完成待辦[/bold]")
            for t in todos:
                due = t.due_time.strftime("%m-%d %H:%M") if t.due_time else "—"
                console.print(f"  • {t.title}  ({t.course_name})  {due}")
        else:
            console.print("\n[green]沒有未完成待辦[/green]")
        console.print("\n[bold]課程[/bold]")
        for c in courses:
            console.print(f"  {c.id}  {c.name}  {c.teacher_name}")

    run_async_command(_run())
