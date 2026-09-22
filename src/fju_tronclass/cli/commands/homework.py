"""fjumcp homework 子指令。"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="課程作業相關操作。")
console = Console()


@app.command("list")
def list_homework_cmd(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程作業。"""
    from fju_tronclass.services.people import list_homework as _list

    async def _run() -> None:
        async with build_client() as client:
            items = await _list(client, course_id=course_id)

        if as_json:
            emit_json(
                [
                    {
                        "id": h.id,
                        "title": h.title,
                        "type": h.type,
                        "due": h.due,
                        "submitted": h.submitted,
                        "submitted_status": h.submitted_status,
                        "is_closed": h.is_closed,
                        "score": h.score,
                        "group_set_name": h.group_set_name,
                    }
                    for h in items
                ]
            )
            return

        if not items:
            console.print("[dim]這門課沒有作業。[/dim]")
            return

        table = Table(title=f"課程 {course_id} 作業", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("標題", style="bold")
        table.add_column("截止", width=20)
        table.add_column("繳交", width=8)
        table.add_column("成績", width=8)
        for h in items:
            due = h.due.strftime("%Y-%m-%d %H:%M") if h.due else "—"
            submitted = "[green]已繳[/green]" if h.submitted else "[yellow]未繳[/yellow]"
            score = "—" if h.score is None else str(h.score)
            table.add_row(str(h.id), h.title, due, submitted, score)
        console.print(table)
        console.print(f"共 [bold]{len(items)}[/bold] 筆")

    run_async_command(_run())


@app.command("show")
def show_homework(
    homework_id: int = typer.Argument(..., help="作業 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示作業說明。"""
    from fju_tronclass.models.catalog import html_to_text

    async def _run() -> None:
        async with build_client() as client:
            data = await client.get_homework(homework_id)
        if as_json:
            emit_json(data)
            return
        payload = data.get("data")
        if not isinstance(payload, dict):
            payload = {}
        console.print(f"[bold]{data.get('title')}[/bold]  #{data.get('id')}")
        console.print(
            f"截止 {data.get('end_time') or data.get('deadline')}　"
            f"已繳 {data.get('submitted')}　成績 {data.get('score')}"
        )
        desc = html_to_text(str(payload.get("description") or ""))
        if desc:
            console.print("\n" + desc[:2000])


@app.command("submissions")
def homework_submissions(
    homework_id: int = typer.Argument(..., help="作業（activity）ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出本人在此作業的繳交記錄（含草稿）。"""
    from fju_tronclass.services.homework import list_my_submissions

    async def _run() -> None:
        async with build_client() as client:
            items = await list_my_submissions(client, homework_id)

        if as_json:
            emit_json(items)
            return

        if not items:
            console.print("[dim]此作業尚無任何繳交或草稿記錄。[/dim]")
            return

        table = Table(title=f"作業 {homework_id} 繳交記錄", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("狀態", width=10)
        table.add_column("繳交時間", width=20)
        table.add_column("附件")
        for s in items:
            sid = str(s.get("id", "—"))
            if s.get("is_draft"):
                status = "[cyan]草稿[/cyan]"
            elif s.get("marked_submitted"):
                status = "[green]已繳[/green]"
            else:
                status = "[yellow]未知[/yellow]"
            submitted_at = str(s.get("submitted_at") or s.get("created_at") or "—")
            uploads = ", ".join(
                f"{u.get('name')}（{u.get('id')}）" for u in s.get("uploads") or []
            )
            table.add_row(sid, status, submitted_at, uploads or "—")
        console.print(table)
        console.print(f"共 [bold]{len(items)}[/bold] 筆")

    run_async_command(_run())


@app.command("upload")
def homework_upload(
    homework_id: int = typer.Argument(..., help="作業（activity）ID"),
    file: Path = typer.Argument(..., help="要上傳的檔案路徑"),
    comment: str = typer.Option("", "--comment", "-c", help="附帶說明文字（選填）"),
    poll_timeout: float = typer.Option(120.0, "--poll-timeout", help="等待轉檔完成的秒數"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """
    上傳檔案並存入作業草稿（只存草稿，不會正式繳交）。

    正式繳交請登入 TronClass 網頁，於作業頁按「繳交作業」。
    """
    from fju_tronclass.services.homework import upload_homework_draft

    async def _run() -> None:
        async with build_client() as client:
            result = await upload_homework_draft(
                client,
                homework_id,
                file,
                comment=comment,
                poll_timeout=poll_timeout,
            )

        if as_json:
            emit_json(result)
            return

        status = "已更新既有草稿" if result["draft_updated"] else "已建立新草稿"
        console.print(
            f"[green]✓ {status}[/green]：附件 {result['upload_name']}"
            f"（{result['upload_size']} bytes，upload id {result['upload_id']}）"
        )
        if result["submission_id"]:
            console.print(f"草稿 submission id：{result['submission_id']}")
        console.print("[dim]提醒：尚未正式繳交，請至 TronClass 網頁確認後按「繳交作業」。[/dim]")

    run_async_command(_run())
