"""fjumcp activities 子指令。"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="課程活動（教材、影片）相關操作。")
console = Console()


@app.command("list")
def list_cmd(
    course_id: int = typer.Argument(..., help="課程 ID（從 fjumcp courses list 取得）"),
    videos_only: bool = typer.Option(False, "--videos", help="只顯示影片活動"),
    materials_only: bool = typer.Option(False, "--materials", help="只顯示教材活動"),
) -> None:
    """列出課程中所有活動（教材與影片）。"""

    async def _run() -> None:
        async with build_client() as client:
            activities = await client.get_course_activities(course_id)

        filtered = activities
        if videos_only:
            filtered = [a for a in activities if a.is_video]
        elif materials_only:
            filtered = [a for a in activities if a.is_material]

        if not filtered:
            console.print("[dim]沒有符合條件的活動。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 活動清單", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("名稱", min_width=20)
        table.add_column("類型", width=12)
        table.add_column("完成", width=6)
        table.add_column("時長/附件")

        for a in filtered:
            type_label = "[cyan]影片[/cyan]" if a.is_video else "[yellow]教材[/yellow]"
            done_label = "[green]✓[/green]" if a.is_complete else "[dim]✗[/dim]"
            if a.is_video and a.video_duration:
                extra = f"{a.video_duration}s"
            elif a.is_material and a.uploads:
                extra = f"{len(a.uploads)} 個附件"
            else:
                extra = ""
            table.add_row(str(a.id), a.display_name, type_label, done_label, extra)

        console.print(table)

        # 如果是教材且有附件，顯示 upload IDs
        mat_with_uploads = [a for a in filtered if a.is_material and a.uploads]
        if mat_with_uploads:
            console.print("\n[bold]教材附件清單（用於 fjumcp download upload）：[/bold]")
            for a in mat_with_uploads:
                for u in a.uploads:
                    size_mb = u.size / 1_048_576
                    console.print(f"  upload {u.id}  {u.name}  ({size_mb:.1f} MB)")

    asyncio.run(_run())
