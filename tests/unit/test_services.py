"""unit tests for services/courses.py、todos.py、bulletins.py。"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from fju_tronclass.models.bulletin import Bulletin
from fju_tronclass.models.course import Course
from fju_tronclass.models.todo import Todo


def _make_course(id: int, semester: str = "113-2") -> Course:
    return Course(id=id, name=f"課程{id}", semester=semester)


def _make_todo(id: int, is_done: bool = False) -> Todo:
    return Todo(id=id, title=f"作業{id}", course_id=1, is_done=is_done)


def _make_bulletin(id: int, course_id: int = 10) -> Bulletin:
    return Bulletin(id=id, title=f"公告{id}", course_id=course_id)


# ------------------------------------------------------------------ #
# courses
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_list_courses_no_filter() -> None:
    from fju_tronclass.services.courses import list_courses

    client = AsyncMock()
    client.get_my_courses.return_value = [
        _make_course(1, "113-2"),
        _make_course(2, "113-1"),
    ]
    result = await list_courses(client)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_courses_filters_by_semester() -> None:
    from fju_tronclass.services.courses import list_courses

    client = AsyncMock()
    client.get_my_courses.return_value = [
        _make_course(1, "113-2"),
        _make_course(2, "113-1"),
    ]
    result = await list_courses(client, semester="113-2")
    assert len(result) == 1
    assert result[0].id == 1


# ------------------------------------------------------------------ #
# todos
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_list_todos_excludes_done_by_default() -> None:
    from fju_tronclass.services.todos import list_todos

    client = AsyncMock()
    client.get_todos.return_value = [
        _make_todo(1, is_done=False),
        _make_todo(2, is_done=True),
    ]
    result = await list_todos(client)
    assert len(result) == 1
    assert result[0].id == 1


@pytest.mark.asyncio
async def test_list_todos_include_done() -> None:
    from fju_tronclass.services.todos import list_todos

    client = AsyncMock()
    client.get_todos.return_value = [
        _make_todo(1, is_done=False),
        _make_todo(2, is_done=True),
    ]
    result = await list_todos(client, include_done=True)
    assert len(result) == 2


# ------------------------------------------------------------------ #
# bulletins
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_list_bulletins_returns_limited() -> None:
    from fju_tronclass.services.bulletins import list_bulletins

    client = AsyncMock()
    client.get_course_bulletins.return_value = [_make_bulletin(i) for i in range(30)]
    result = await list_bulletins(client, course_id=10, limit=5)
    assert len(result) == 5


@pytest.mark.asyncio
async def test_list_bulletins_default_limit() -> None:
    from fju_tronclass.services.bulletins import list_bulletins

    client = AsyncMock()
    client.get_course_bulletins.return_value = [_make_bulletin(i) for i in range(25)]
    result = await list_bulletins(client, course_id=10)
    assert len(result) == 20
