"""unit tests for MCP tool handler bodies (mocked client)."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from fju_tronclass.models.activity import (
    Activity,
    ActivityListResponse,
    ActivityReadRanges,
    ActivityReadResult,
)
from fju_tronclass.models.bulletin import Bulletin
from fju_tronclass.models.course import Course
from fju_tronclass.models.todo import Todo
from fju_tronclass.services.search import UploadSearchResult
from fju_tronclass.services.video import VideoMarkResult

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


def _load_activities() -> list[Activity]:
    data = json.loads((FIXTURE_DIR / "course_activities.json").read_text(encoding="utf-8"))
    return ActivityListResponse.model_validate(data).items


def _make_ctx(client: AsyncMock):  # type: ignore[no-untyped-def]
    """Build a mock async context manager for get_client()."""
    @asynccontextmanager
    async def _ctx() -> AsyncGenerator[AsyncMock, None]:
        yield client

    return _ctx


# ------------------------------------------------------------------ #
# activity_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_list_course_activities_returns_summary() -> None:
    from fju_tronclass.mcp_server.tools.activity_tools import fju_list_course_activities

    activities = _load_activities()
    client = AsyncMock()
    client.get_course_activities.return_value = activities

    with patch(
        "fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)
    ):
        result = await fju_list_course_activities(course_id=10001)

    assert len(result) == 4
    assert result[0]["id"] == 40001


@pytest.mark.asyncio
async def test_fju_search_and_download_downloads_files() -> None:
    from fju_tronclass.mcp_server.tools.activity_tools import fju_search_and_download

    search_results = [
        UploadSearchResult(
            upload_id=50001,
            upload_name="第一週講義.pdf",
            upload_size=1_048_576,
            activity_id=40001,
            activity_name="第一週教材",
            course_id=10001,
            course_name="資料結構",
            activity_type="material",
        )
    ]
    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.search.search_uploads_by_keyword",
            new_callable=AsyncMock,
            return_value=search_results,
        ),
        patch(
            "fju_tronclass.services.downloads.download_upload",
            new_callable=AsyncMock,
            return_value=(Path("/tmp/第一週講義.pdf"), 1_048_576),
        ),
    ):
        result = await fju_search_and_download(keyword="第一週", course_id=10001)

    assert result["found"] == 1
    assert result["downloaded"] == 1


@pytest.mark.asyncio
async def test_fju_search_and_download_no_results() -> None:
    from fju_tronclass.mcp_server.tools.activity_tools import fju_search_and_download

    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.search.search_uploads_by_keyword",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await fju_search_and_download(keyword="不存在xyz", course_id=10001)

    assert result["found"] == 0
    assert result["downloaded"] == 0


@pytest.mark.asyncio
async def test_fju_batch_mark_videos_complete_returns_summary() -> None:
    from fju_tronclass.mcp_server.tools.activity_tools import fju_batch_mark_videos_complete

    video_results = [
        VideoMarkResult(
            activity_id=40004, activity_name="課程影片2", duration=1200,
            completeness_pct=100, success=True
        ),
    ]
    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.video.mark_all_videos_in_course",
            new_callable=AsyncMock,
            return_value=video_results,
        ),
    ):
        result = await fju_batch_mark_videos_complete(course_id=10001)

    assert result["total"] == 1
    assert result["success"] == 1
    assert result["failed"] == 0


# ------------------------------------------------------------------ #
# course_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_list_courses_returns_list() -> None:
    from fju_tronclass.mcp_server.tools.course_tools import fju_list_courses

    courses = [
        Course(id=10001, name="資料結構", semester="113-2"),
        Course(id=10002, name="計算機網路", semester="113-2"),
    ]
    client = AsyncMock()
    client.get_my_courses.return_value = courses

    with patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)):
        result = await fju_list_courses()

    assert len(result) == 2
    assert result[0]["id"] == 10001


@pytest.mark.asyncio
async def test_fju_list_courses_filters_by_semester() -> None:
    from fju_tronclass.mcp_server.tools.course_tools import fju_list_courses

    courses = [
        Course(id=10001, name="資料結構", semester="113-2"),
        Course(id=10002, name="舊課", semester="112-1"),
    ]
    client = AsyncMock()
    client.get_my_courses.return_value = courses

    with patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)):
        result = await fju_list_courses(semester="113-2")

    assert len(result) == 1
    assert result[0]["id"] == 10001


# ------------------------------------------------------------------ #
# todo_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_list_todos_excludes_done_by_default() -> None:
    from fju_tronclass.mcp_server.tools.todo_tools import fju_list_todos

    todos = [
        Todo(id=1, title="作業一", is_done=False, course_id=10001, course_name="資料結構"),
        Todo(id=2, title="作業二", is_done=True, course_id=10001, course_name="資料結構"),
    ]
    client = AsyncMock()
    client.get_todos.return_value = todos

    with patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)):
        result = await fju_list_todos()

    assert len(result) == 1
    assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_fju_list_todos_includes_done_when_flag_set() -> None:
    from fju_tronclass.mcp_server.tools.todo_tools import fju_list_todos

    todos = [
        Todo(id=1, title="作業一", is_done=False, course_id=10001, course_name="資料結構"),
        Todo(id=2, title="作業二", is_done=True, course_id=10001, course_name="資料結構"),
    ]
    client = AsyncMock()
    client.get_todos.return_value = todos

    with patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)):
        result = await fju_list_todos(include_done=True)

    assert len(result) == 2


# ------------------------------------------------------------------ #
# bulletin_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_list_course_bulletins_returns_limited() -> None:
    from fju_tronclass.mcp_server.tools.bulletin_tools import fju_list_course_bulletins

    bulletins = [
        Bulletin(id=i, title=f"公告{i}", content=f"內容{i}", course_id=10001)
        for i in range(1, 6)
    ]
    client = AsyncMock()
    client.get_course_bulletins.return_value = bulletins

    with patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)):
        result = await fju_list_course_bulletins(course_id=10001, limit=3)

    assert len(result) == 3


# ------------------------------------------------------------------ #
# download_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_download_upload_returns_path_and_size() -> None:
    from fju_tronclass.mcp_server.tools.download_tools import fju_download_upload

    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.downloads.download_upload",
            new_callable=AsyncMock,
            return_value=(Path("/tmp/lecture.pdf"), 2_097_152),
        ),
    ):
        result = await fju_download_upload(upload_id=50001)

    assert result["size_bytes"] == 2_097_152
    assert "lecture.pdf" in result["path"]


# ------------------------------------------------------------------ #
# video_tools
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_fju_mark_video_complete_success() -> None:
    from fju_tronclass.mcp_server.tools.video_tools import fju_mark_video_complete

    read_result = ActivityReadResult(
        completeness="full",
        data=ActivityReadRanges(completeness=100),
    )
    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.video.mark_video_complete",
            new_callable=AsyncMock,
            return_value=read_result,
        ),
    ):
        result = await fju_mark_video_complete(activity_id=40004, duration_seconds=1200)

    assert result["completeness"] == "full"
    assert result["completeness_pct"] == 100


@pytest.mark.asyncio
async def test_fju_mark_video_complete_zero_duration() -> None:
    from fju_tronclass.mcp_server.tools.video_tools import fju_mark_video_complete

    client = AsyncMock()

    with (
        patch("fju_tronclass.mcp_server._client_factory.get_client", _make_ctx(client)),
        patch(
            "fju_tronclass.services.video.mark_video_complete",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await fju_mark_video_complete(activity_id=40004, duration_seconds=0)

    assert result["completeness"] == "none"
    assert result["completeness_pct"] == 0
