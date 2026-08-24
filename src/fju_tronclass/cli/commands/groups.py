"""fjumcp groups 子指令。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from fju_tronclass.cli._helpers import build_client, run_async_command
from fju_tronclass.cli._output import emit_json

app = typer.Typer(help="課程分組相關操作。")
console = Console()


@app.command("list")
def list_groups_cmd(
    course_id: int = typer.Argument(..., help="課程 ID"),
    as_json: bool = typer.Option(False, "--json", help="以 JSON 輸出"),
) -> None:
    """列出課程分組（官方 students.group_ids 聚合，不掃 ID）。"""
    from fju_tronclass.services.people import list_groups as _list

    async def _run() -> None:
        async with build_client() as client:
            sets = await _list(client, course_id=course_id)

        if as_json:
            emit_json(
                [
                    {
                        "id": s.id,
                        "name": s.name,
                        "group_count": s.group_count,
                        "groups": [
                            {
                                "id": g.id,
                                "name": g.name,
                                "sort": g.sort,
                                "members": [
                                    {"id": m.id, "name": m.name, "user_no": m.user_no} for m in g.members
                                ],
                            }
                            for g in s.groups
                        ],
                    }
                    for s in sets
                ]
            )
            return

        if not sets:
            console.print("[dim]這門課沒有分組。[/dim]")
            return

        for gset in sets:
            title = gset.name or f"group-set {gset.id}"
            table = Table(title=f"{title}（{len(gset.groups)}/{gset.group_count} 組）", show_lines=True)
            table.add_column("組 ID", style="dim", width=10)
            table.add_column("組名", width=12)
            table.add_column("人數", width=6)
            table.add_column("成員")
            for g in gset.groups:
                members = "、".join(f"{m.name}({m.user_no})" if m.user_no else m.name for m in g.members)
                table.add_row(str(g.id), g.name or "—", str(len(g.members)), members)
            console.print(table)

    run_async_command(_run())
