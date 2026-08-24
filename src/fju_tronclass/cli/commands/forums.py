"""fjumcp forums。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json
from fju_tronclass.models.catalog import html_to_text

app = typer.Typer(help="討論區。")
console = Console()


@app.command("topics")
def list_topics(
    activity_id: int = typer.Argument(..., help="討論活動 ID（activities list 的 forum）"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出討論區主題。"""

    async def _run() -> None:
        async with build_client() as client:
            topics = await client.get_forum_topics(activity_id)
        if as_json:
            emit_json([t.model_dump() for t in topics])
            return
        if not topics:
            console.print("[dim]沒有主題。[/dim]")
            return
        table = Table(title=f"討論 {activity_id}", show_lines=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("標題")
        table.add_column("作者", width=10)
        table.add_column("讚", width=4)
        table.add_column("內容")
        for topic in topics:
            table.add_row(
                str(topic.id),
                topic.title,
                topic.author,
                str(topic.like_count),
                html_to_text(topic.content)[:60],
            )
        console.print(table)
        console.print(f"共 [bold]{len(topics)}[/bold] 則")

    run_async_command(_run())


@app.command("topic")
def show_topic(
    topic_id: int = typer.Argument(..., help="主題 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """顯示討論主題詳情。"""

    async def _run() -> None:
        async with build_client() as client:
            data = await client.get_topic(topic_id)
        if as_json:
            emit_json(data)
            return
        created = data.get("created_by")
        if not isinstance(created, dict):
            created = {}
        console.print(f"[bold]{data.get('title') or '(無標題)'}[/bold]  #{data.get('id')}")
        console.print(f"作者：{created.get('name', '—')}　讚 {data.get('like_count', 0)}")
        console.print(html_to_text(str(data.get("content") or "")))

    run_async_command(_run())
