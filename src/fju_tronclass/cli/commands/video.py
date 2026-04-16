"""fjumcp video 子指令。"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client
from fju_tronclass.services.video import CHUNK_SIZE

app = typer.Typer(help="影片觀看相關操作。")
console = Console()


@app.command("mark-complete")
def mark_complete_cmd(
    activity_id: int = typer.Argument(..., help="活動 ID"),
    duration: int = typer.Argument(..., help="影片時長（秒）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="僅顯示會執行的分段，不實際呼叫 API"),
) -> None:
    """
    將指定活動的影片標記為完整觀看。

    注意：此操作會繞過觀看驗證機制，會增加完成度但不增加學習時數。
    請自行評估是否符合課程規範，使用者須為自己的學業誠信負責。
    """
    from fju_tronclass.services.video import mark_video_complete

    if dry_run:
        _show_dry_run(activity_id, duration)
        return

    async def _run() -> None:
        async with build_client() as client:
            result = await mark_video_complete(client, activity_id=activity_id, duration=duration)

        if result:
            completeness = result.data.completeness
            console.print(f"[green]✓[/green] 活動 {activity_id} 標記完成，完成度：{completeness}%")
        else:
            console.print(f"[dim]活動 {activity_id} duration=0，無需操作。[/dim]")

    asyncio.run(_run())


def _show_dry_run(activity_id: int, duration: int) -> None:
    """Dry-run：顯示分段資訊而不呼叫 API。"""
    console.print(f"[bold][DRY RUN][/bold] 活動 {activity_id}，時長 {duration} 秒")

    if duration <= 0:
        console.print("[dim]duration=0，無需分段。[/dim]")
        return

    table = Table(title=f"預計分段（共 {-(-duration // CHUNK_SIZE)} 段）", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("start（秒）", width=12)
    table.add_column("end（秒）", width=12)
    table.add_column("duration（秒）", width=16)
    table.add_column("chunk 大小", width=12)

    seg = 1
    start = 0
    while start < duration:
        end = min(start + CHUNK_SIZE, duration)
        table.add_row(str(seg), str(start), str(end), str(duration), str(end - start))
        start = end
        seg += 1

    console.print(table)
    console.print("[yellow]加上 --apply 旗標（移除 --dry-run）即實際執行。[/yellow]")
