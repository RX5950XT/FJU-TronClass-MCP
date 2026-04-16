"""fjumcp download 子指令。"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="教材下載相關操作。")
console = Console()


@app.command("upload")
def download_upload_cmd(
    upload_id: int = typer.Argument(..., help="Upload ID"),
    dest: Path = typer.Option(
        None, "--dest", "-d", help="下載目標目錄（預設：~/Downloads/TronClass）"
    ),
) -> None:
    """下載指定 upload（即使設為不允許下載的教材也可下載）。"""
    from fju_tronclass.config import get_settings
    from fju_tronclass.services.downloads import download_upload

    settings = get_settings()
    dest_dir = dest or settings.fjumcp_download_dir

    async def _run() -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"下載 upload {upload_id}…", total=None)
            async with build_client() as client:
                file_path, size = await download_upload(
                    client, upload_id=upload_id, dest_dir=dest_dir
                )
            progress.update(task, completed=True)

        size_mb = size / 1_048_576
        console.print(f"[green]✓[/green] 下載完成：{file_path}")
        console.print(f"  大小：{size_mb:.2f} MB")

    asyncio.run(_run())


@app.command("search")
def search_and_download_cmd(
    keyword: str = typer.Argument(..., help="搜尋關鍵字（檔案名稱或活動名稱的片段）"),
    course_id: int = typer.Option(None, "--course", "-c", help="指定課程 ID（不填則需加 --all）"),
    all_courses: bool = typer.Option(False, "--all", help="跨所有課程搜尋（較慢）"),
    dest: Path = typer.Option(None, "--dest", "-d", help="下載目標目錄"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只列出搜尋結果，不實際下載"),
) -> None:
    """
    依關鍵字搜尋課程教材並下載，不需要知道 upload ID。

    範例：
      fjumcp download search "第三週" --course 101
      fjumcp download search "排序" --all --dry-run
    """
    from fju_tronclass.config import get_settings
    from fju_tronclass.services.downloads import download_upload
    from fju_tronclass.services.search import search_uploads_by_keyword

    if course_id is None and not all_courses:
        console.print("[red]請指定 --course COURSE_ID 或加上 --all 搜尋全部課程[/red]")
        raise typer.Exit(1) from None

    settings = get_settings()
    dest_dir = dest or settings.fjumcp_download_dir

    async def _run() -> None:
        async with build_client() as client:
            results = await search_uploads_by_keyword(
                client,
                keyword=keyword,
                course_id=course_id,
                include_all_courses=all_courses,
            )

        if not results:
            console.print(f"[yellow]找不到含有「{keyword}」的教材。[/yellow]")
            return

        # 顯示搜尋結果
        table = Table(title=f"搜尋「{keyword}」結果", show_lines=True)
        table.add_column("Upload ID", style="dim", width=12)
        table.add_column("檔案名稱", min_width=20)
        table.add_column("活動名稱")
        table.add_column("大小", width=10)

        for r in results:
            size_mb = r.upload_size / 1_048_576
            table.add_row(str(r.upload_id), r.upload_name, r.activity_name, f"{size_mb:.1f} MB")

        console.print(table)

        if dry_run:
            console.print(f"\n[dim]共 {len(results)} 個檔案。移除 --dry-run 即實際下載。[/dim]")
            return

        # 實際下載
        console.print(f"\n開始下載 {len(results)} 個檔案…")
        async with build_client() as client:
            for r in results:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True,
                ) as progress:
                    task = progress.add_task(f"下載 {r.upload_name}…", total=None)
                    try:
                        file_path, size = await download_upload(
                            client, upload_id=r.upload_id, dest_dir=dest_dir
                        )
                        progress.update(task, completed=True)
                        size_mb = size / 1_048_576
                        console.print(f"  [green]✓[/green] {r.upload_name} → {file_path} ({size_mb:.2f} MB)")
                    except Exception as exc:
                        progress.update(task, completed=True)
                        console.print(f"  [red]✗[/red] {r.upload_name}：{exc}")

    asyncio.run(_run())

