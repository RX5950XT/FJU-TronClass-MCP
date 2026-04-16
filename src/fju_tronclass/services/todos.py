"""待辦事項服務。"""

from __future__ import annotations

from fju_tronclass.models.todo import Todo


async def list_todos(client: object, include_done: bool = False) -> list[Todo]:
    """取得待辦事項。"""
    todos: list[Todo] = await client.get_todos()  # type: ignore[attr-defined]
    if not include_done:
        todos = [t for t in todos if not t.is_done]
    return todos
