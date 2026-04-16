"""fjumcp download 子指令。"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from fju_tronclass.cli._helpers import build_client

app = typer.Typer(help="教材下載相關操作。")
console = Console()


@app.command("upload")
def download_upload_cmd(
    upload_id: int = typer.Argument(..., help="Upload ID"),
    dest: Path = typer.Option(
        None, "--dest", "-d", help="下載目標目錄（預設：~/Downloads/TronClass）"
    ),  # noqa: B008
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
