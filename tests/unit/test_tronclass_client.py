"""unit tests for client/tronclass.py"""

from __future__ import annotations

import pytest
import pytest_httpx

from tests.conftest import load_fixture


@pytest.fixture
def client(fake_cookie: str, base_url: str):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.http import TronClassHttp
    from fju_tronclass.client.tronclass import TronClassClient
    return TronClassClient(TronClassHttp(session_cookie=fake_cookie, base_url=base_url))


@pytest.mark.asyncio
async def test_get_my_courses_parses_fixture(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/my-courses?page=1&page_size=20",
        json=load_fixture("my_courses.json"),
    )
    courses = await client.get_my_courses()
    assert len(courses) == 2
    assert all(hasattr(c, "id") for c in courses)
    assert courses[0].name == "資料結構"
    assert courses[1].name == "通訊原理"


@pytest.mark.asyncio
async def test_get_todos_parses_fixture(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/todos",
        json=load_fixture("todos.json"),
    )
    todos = await client.get_todos()
    assert len(todos) == 2
    assert todos[0].title == "第三週作業：鏈結串列實作"
    assert todos[0].is_done is False


@pytest.mark.asyncio
async def test_get_upload_url_parses_fixture(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/uploads/30001/url",
        json=load_fixture("upload_url.json"),
    )
    upload_url = await client.get_upload_url(30001)
    assert upload_url.url.startswith("https://")


@pytest.mark.asyncio
async def test_get_upload_meta_parses_fixture(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/uploads/30001",
        json=load_fixture("upload_meta.json"),
    )
    meta = await client.get_upload_meta(30001)
    assert meta.name == "第三週講義.pdf"
    assert meta.allow_download is False


@pytest.mark.asyncio
async def test_post_activity_read_parses_fixture(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/course/activities-read/40001",
        json=load_fixture("activities_read.json"),
    )
    result = await client.post_activity_read(40001, start=0, end=90, duration=177)
    assert result.data.completeness == 100
