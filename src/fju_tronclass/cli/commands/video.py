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


@app.command("batch-complete")
def batch_complete_cmd(
    course_id: int = typer.Argument(..., help="課程 ID（從 fjumcp courses list 取得）"),
    include_completed: bool = typer.Option(False, "--include-completed", help="包含已完成的影片（重新標記）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只顯示會處理的影片，不實際呼叫 API"),
) -> None:
    """
    一次標記課程中所有影片為完整觀看（不需逐一提供 activity_id）。

    注意：此操作繞過觀看驗證，使用者須自行評估學業誠信風險。
    建議先用 --dry-run 確認影片清單。
    """
    from fju_tronclass.services.video import mark_all_videos_in_course

    async def _dry_run() -> None:
        from fju_tronclass.models.activity import Activity

        async with build_client() as client:
            activities = await client.get_course_activities(course_id)

        videos: list[Activity] = [
            a for a in activities
            if a.is_video and a.video_duration is not None and a.video_duration > 0
        ]
        pending = [a for a in videos if not a.is_complete] if not include_completed else videos

        table = Table(title=f"課程 {course_id} 待標記影片（共 {len(pending)} 部）", show_lines=True)
        table.add_column("Activity ID", style="dim", width=14)
        table.add_column("名稱", min_width=20)
        table.add_column("時長", width=10)
        table.add_column("目前完成度", width=12)
        table.add_column("分段數", width=8)

        for a in pending:
            dur = a.video_duration or 0
            chunks = max(0, -(-dur // CHUNK_SIZE))
            table.add_row(str(a.id), a.display_name, f"{dur}s", f"{a.completeness}%", str(chunks))

        console.print(table)
        console.print("[yellow]移除 --dry-run 即實際執行標記。[/yellow]")

    async def _run() -> None:
        skip = not include_completed
        with console.status(f"正在標記課程 {course_id} 所有影片…"):
            async with build_client() as client:
                results = await mark_all_videos_in_course(
                    client, course_id=course_id, skip_completed=skip
                )

        table = Table(title=f"課程 {course_id} 批量標記結果", show_lines=True)
        table.add_column("Activity ID", style="dim", width=14)
        table.add_column("名稱", min_width=20)
        table.add_column("時長", width=10)
        table.add_column("完成度", width=10)
        table.add_column("狀態", width=8)

        for r in results:
            status = "[green]✓[/green]" if r.success else f"[red]✗ {r.error}[/red]"
            table.add_row(str(r.activity_id), r.activity_name, f"{r.duration}s",
                          f"{r.completeness_pct}%", status)

        console.print(table)
        success = sum(1 for r in results if r.success)
        console.print(
            f"\n共 {len(results)} 部影片，[green]成功 {success} 部[/green]，"
            f"[red]失敗 {len(results) - success} 部[/red]"
        )

    if dry_run:
        asyncio.run(_dry_run())
    else:
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
