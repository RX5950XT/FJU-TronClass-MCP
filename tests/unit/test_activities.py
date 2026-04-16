"""unit tests for services/search.py and extended Activity model。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from fju_tronclass.models.activity import (
    Activity,
    ActivityData,
    ActivityListResponse,
    ActivityUpload,
)

# ------------------------------------------------------------------ #
# Activity model 測試
# ------------------------------------------------------------------ #

FIXTURE = Path(__file__).parent.parent / "fixtures" / "course_activities.json"


def _load_activities() -> list[Activity]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return ActivityListResponse.model_validate(data).items


def test_activity_list_response_parses_fixture() -> None:
    activities = _load_activities()
    assert len(activities) == 4


def test_material_activity_has_uploads() -> None:
    activities = _load_activities()
    material = next(a for a in activities if a.is_material)
    assert len(material.uploads) > 0
    assert material.uploads[0].id == 50001


def test_video_activity_has_duration() -> None:
    activities = _load_activities()
    video = next(a for a in activities if a.is_video)
    assert video.video_duration is not None
    assert video.video_duration > 0


def test_completed_video_is_complete() -> None:
    activities = _load_activities()
    # ID 40003 有 completenessTip="已完成"
    completed = next(a for a in activities if a.id == 40003)
    assert completed.is_complete is True


def test_incomplete_video_is_not_complete() -> None:
    activities = _load_activities()
    incomplete = next(a for a in activities if a.id == 40004)
    assert incomplete.is_complete is False


def test_display_name_prefers_title_for_video() -> None:
    act = Activity(id=1, name="", title="影片標題", type="online_video")
    assert act.display_name == "影片標題"


def test_display_name_falls_back_to_name() -> None:
    act = Activity(id=1, name="教材名稱", title="", type="material")
    assert act.display_name == "教材名稱"


def test_activity_data_duration_via_property() -> None:
    act = Activity(id=1, title="test", type="online_video", data=ActivityData(duration=300))
    assert act.video_duration == 300


def test_activity_upload_fields() -> None:
    upload = ActivityUpload(id=99, name="test.pdf", size=1024)
    assert upload.id == 99
    assert upload.name == "test.pdf"
    assert upload.size == 1024


# ------------------------------------------------------------------ #
# search service 測試
# ------------------------------------------------------------------ #

def _make_activities_client() -> AsyncMock:
    activities = _load_activities()
    client = AsyncMock()
    client.get_course_activities.return_value = activities
    return client


@pytest.mark.asyncio
async def test_search_finds_by_upload_name() -> None:
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = _make_activities_client()
    results = await search_uploads_by_keyword(client, "第一週講義.pdf", course_id=10001)

    assert len(results) == 1
    assert results[0].upload_name == "第一週講義.pdf"
    assert results[0].upload_id == 50001


@pytest.mark.asyncio
async def test_search_finds_by_activity_name() -> None:
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = _make_activities_client()
    # 活動名稱含「第一週」，其下有兩個 upload
    results = await search_uploads_by_keyword(client, "第一週", course_id=10001)

    assert len(results) == 2
    upload_ids = {r.upload_id for r in results}
    assert 50001 in upload_ids
    assert 50002 in upload_ids


@pytest.mark.asyncio
async def test_search_case_insensitive() -> None:
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = _make_activities_client()
    # 搜尋「PDF」（大寫），應與小寫「.pdf」比對
    results = await search_uploads_by_keyword(client, "PDF", course_id=10001)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_no_result_returns_empty() -> None:
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = _make_activities_client()
    results = await search_uploads_by_keyword(client, "不存在的關鍵字xyz", course_id=10001)
    assert results == []


@pytest.mark.asyncio
async def test_search_videos_not_included() -> None:
    """影片活動沒有 uploads，不應出現在搜尋結果中。"""
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = _make_activities_client()
    # 搜尋影片標題關鍵字，但影片沒有 uploads，所以應回傳空
    results = await search_uploads_by_keyword(client, "課程影片", course_id=10001)
    assert results == []


@pytest.mark.asyncio
async def test_search_requires_course_id_or_all_flag() -> None:
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = AsyncMock()
    with pytest.raises(ValueError, match="course_id"):
        await search_uploads_by_keyword(client, "test")


@pytest.mark.asyncio
async def test_search_all_courses(monkeypatch: pytest.MonkeyPatch) -> None:
    from fju_tronclass.models.course import Course
    from fju_tronclass.services.search import search_uploads_by_keyword

    activities = _load_activities()
    client = AsyncMock()
    client.get_my_courses.return_value = [Course(id=10001, name="資料結構", semester="113-2")]
    client.get_course_activities.return_value = activities

    results = await search_uploads_by_keyword(
        client, "第一週", include_all_courses=True
    )
    assert len(results) >= 1
    client.get_my_courses.assert_called_once()


@pytest.mark.asyncio
async def test_search_skips_course_on_exception() -> None:
    """當取得活動失敗時，應跳過該課程而非拋出例外。"""
    from fju_tronclass.models.course import Course
    from fju_tronclass.services.search import search_uploads_by_keyword

    client = AsyncMock()
    client.get_my_courses.return_value = [
        Course(id=10001, name="資料結構"),
        Course(id=10002, name="通訊原理"),
    ]
    # 第一個課程正常，第二個拋出例外
    activities = _load_activities()
    client.get_course_activities.side_effect = [activities, Exception("network error")]

    results = await search_uploads_by_keyword(client, "第一週", include_all_courses=True)
    # 只有第一個課程的結果
    assert len(results) >= 1


# ------------------------------------------------------------------ #
# batch video service 測試
# ------------------------------------------------------------------ #

def _make_video_client(activities: list[Activity]) -> AsyncMock:
    client = AsyncMock()
    client.get_course_activities.return_value = activities
    from fju_tronclass.models.activity import ActivityReadRanges, ActivityReadResult
    client.post_activity_read.return_value = ActivityReadResult(
        completeness="full",
        data=ActivityReadRanges(completeness=100),
    )
    return client


@pytest.mark.asyncio
async def test_batch_mark_skips_completed_by_default() -> None:
    from fju_tronclass.services.video import mark_all_videos_in_course

    activities = _load_activities()
    client = _make_video_client(activities)

    results = await mark_all_videos_in_course(client, course_id=10001, skip_completed=True)

    # 活動清單中只有 40004 未完成（40003 已完成）
    incomplete_ids = {r.activity_id for r in results}
    assert 40004 in incomplete_ids
    assert 40003 not in incomplete_ids


@pytest.mark.asyncio
async def test_batch_mark_includes_completed_when_flag_set() -> None:
    from fju_tronclass.services.video import mark_all_videos_in_course

    activities = _load_activities()
    client = _make_video_client(activities)

    results = await mark_all_videos_in_course(client, course_id=10001, skip_completed=False)

    ids = {r.activity_id for r in results}
    assert 40003 in ids
    assert 40004 in ids


@pytest.mark.asyncio
async def test_batch_mark_success_flag() -> None:
    from fju_tronclass.services.video import mark_all_videos_in_course

    activities = _load_activities()
    client = _make_video_client(activities)
    results = await mark_all_videos_in_course(client, course_id=10001, skip_completed=False)

    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_batch_mark_handles_single_failure() -> None:
    from fju_tronclass.services.video import mark_all_videos_in_course

    activities = _load_activities()
    client = AsyncMock()
    client.get_course_activities.return_value = activities
    client.post_activity_read.side_effect = Exception("API error")

    results = await mark_all_videos_in_course(client, course_id=10001, skip_completed=False)

    # 所有影片都應有結果，但 success=False
    video_count = sum(1 for a in activities if a.is_video and a.video_duration)
    assert len(results) == video_count
    assert all(not r.success for r in results)
    assert all(r.error != "" for r in results)
