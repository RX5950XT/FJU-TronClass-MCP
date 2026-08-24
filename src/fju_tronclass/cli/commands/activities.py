"""fjumcp activities 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command

app = typer.Typer(help="課程活動（教材、影片）相關操作。")
console = Console()


@app.command("list")
def list_cmd(
    course_id: int = typer.Argument(..., help="課程 ID（從 fjumcp courses list 取得）"),
    videos_only: bool = typer.Option(False, "--videos", help="只顯示影片活動"),
    materials_only: bool = typer.Option(False, "--materials", help="只顯示教材活動"),
    type_filter: str | None = typer.Option(None, "--type", "-t", help="過濾類型：material/online_video/homework/forum/web_link/page"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程中所有活動。"""

    async def _run() -> None:
        async with build_client() as client:
            activities = await client.get_course_activities(course_id)

        filtered = activities
        if videos_only:
            filtered = [a for a in activities if a.is_video]
        elif materials_only:
            filtered = [a for a in activities if a.is_material]
        elif type_filter:
            filtered = [a for a in activities if a.type == type_filter]

        if as_json:
            from fju_tronclass.cli._output import emit_json

            emit_json(
                [
                    {
                        "id": a.id,
                        "name": a.display_name,
                        "type": a.type,
                        "complete": a.is_complete,
                        "duration": a.video_duration,
                        "link": a.data.link if a.data else "",
                        "uploads": [{"id": u.id, "name": u.name, "size": u.size} for u in a.uploads],
                    }
                    for a in filtered
                ]
            )
            return

        if not filtered:
            console.print("[dim]沒有符合條件的活動。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 活動清單", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("名稱", min_width=20)
        table.add_column("類型", width=12)
        table.add_column("完成", width=6)
        table.add_column("補充")

        for a in filtered:
            done_label = "[green]✓[/green]" if a.is_complete else "[dim]✗[/dim]"
            table.add_row(str(a.id), a.display_name, a.type_label, done_label, a.extra_text)

        console.print(table)

        # 如果是教材且有附件，顯示 upload IDs
        mat_with_uploads = [a for a in filtered if a.is_material and a.uploads]
        if mat_with_uploads:
            console.print("\n[bold]教材附件清單（用於 fjumcp download upload）：[/bold]")
            for a in mat_with_uploads:
                for u in a.uploads:
                    size_mb = u.size / 1_048_576
                    console.print(f"  upload {u.id}  {u.name}  ({size_mb:.1f} MB)")

    run_async_command(_run())


@app.command("show")
def show_activity(
    activity_id: int = typer.Argument(..., help="活動 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示活動詳情（作業說明、連結、頁面內容）。"""
    from fju_tronclass.cli._output import emit_json
    from fju_tronclass.models.catalog import html_to_text

    async def _run() -> None:
        async with build_client() as client:
            data = await client.get_activity(activity_id)
        if as_json:
            emit_json(data)
            return
        payload = data.get("data")
        if not isinstance(payload, dict):
            payload = {}
        console.print(f"[bold]{data.get('title') or data.get('name')}[/bold]  #{data.get('id')}")
        console.print(f"類型 {data.get('type')}　課程 {data.get('course_id')}")
        if payload.get("link"):
            console.print(f"連結 {payload['link']}")
        desc = html_to_text(str(payload.get("description") or payload.get("content") or ""))
        if desc:
            console.print("\n" + desc[:2000])

    run_async_command(_run())
