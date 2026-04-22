"""補充 tronclass.py 的覆蓋率測試：SchemaError 路徑、ValueError、更多 endpoints。"""

from __future__ import annotations

import pytest
import pytest_httpx

from fju_tronclass.errors import SchemaError


@pytest.fixture
def http(fake_cookie: str, base_url: str):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.http import TronClassHttp
    return TronClassHttp(session_cookie=fake_cookie, base_url=base_url)


@pytest.fixture
def client(http):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.tronclass import TronClassClient
    return TronClassClient(http=http)


# ------------------------------------------------------------------ #
# SchemaError：各 endpoint 回傳無法解析的 JSON 時應包裝為 SchemaError
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_get_my_courses_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    # "courses" 欄位給字串會讓 pydantic 無法解析為 list[Course]
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/my-courses?page=1&page_size=20",
        json={"courses": "not-a-list"},
    )
    with pytest.raises(SchemaError):
        await client.get_my_courses()


@pytest.mark.asyncio
async def test_get_todos_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    # "todo_list" 欄位給整數會讓 pydantic 無法解析為 list[Todo]
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/todos",
        json={"todo_list": 42},
    )
    with pytest.raises(SchemaError):
        await client.get_todos()


@pytest.mark.asyncio
async def test_get_course_bulletins_success(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course-bulletins?course_id=101",
        json={"bulletins": [], "total": 0},
    )
    result = await client.get_course_bulletins(101)
    assert result == []


@pytest.mark.asyncio
async def test_get_course_bulletins_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    # "bulletins" 欄位給布林值會讓 pydantic 無法解析為 list[Bulletin]
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course-bulletins?course_id=101",
        json={"bulletins": True},
    )
    with pytest.raises(SchemaError):
        await client.get_course_bulletins(101)


@pytest.mark.asyncio
async def test_get_upload_url_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/uploads/999/url",
        json={"wrong": "structure"},
    )
    with pytest.raises(SchemaError):
        await client.get_upload_url(999)


@pytest.mark.asyncio
async def test_get_upload_meta_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/uploads/999",
        json={"wrong": "structure"},
    )
    with pytest.raises(SchemaError):
        await client.get_upload_meta(999)


@pytest.mark.asyncio
async def test_get_learning_activity_success(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course/10/learning-activity/20",
        json={
            "id": 20,
            "title": "Week 1",
            "type": "video",
            "course_id": 10,
            "duration": 300,
        },
    )
    from fju_tronclass.models.activity import Activity
    result = await client.get_learning_activity(10, 20)
    assert isinstance(result, Activity)
    assert result.id == 20


@pytest.mark.asyncio
async def test_get_learning_activity_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course/10/learning-activity/20",
        json={"bad": "data"},
    )
    with pytest.raises(SchemaError):
        await client.get_learning_activity(10, 20)


@pytest.mark.asyncio
async def test_post_activity_read_raises_value_error_when_chunk_too_large(
    client,  # type: ignore[no-untyped-def]
) -> None:
    with pytest.raises(ValueError, match="125"):
        await client.post_activity_read(
            activity_id=1, start=0, end=126, duration=300
        )


@pytest.mark.asyncio
async def test_post_activity_read_schema_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    # "data" 欄位給字串會讓 pydantic 無法解析為 ActivityReadRanges
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course/activities-read/1",
        method="POST",
        json={"completeness": "full", "data": "not-a-dict"},
    )
    with pytest.raises(SchemaError):
        await client.post_activity_read(
            activity_id=1, start=0, end=90, duration=300
        )
