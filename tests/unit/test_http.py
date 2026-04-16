"""unit tests for client/http.py"""

from __future__ import annotations

import pytest
import pytest_httpx

from fju_tronclass.errors import ClientError, ServerError, SessionExpiredError


@pytest.fixture
def client(fake_cookie: str, base_url: str):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.http import TronClassHttp
    return TronClassHttp(session_cookie=fake_cookie, base_url=base_url)


@pytest.mark.asyncio
async def test_get_json_success(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={"hello": "world"},
    )
    result = await client.get_json("/api/test")
    assert result == {"hello": "world"}


@pytest.mark.asyncio
async def test_get_json_raises_session_expired_on_401(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=401,
        json={"message": "Unauthorized"},
    )
    with pytest.raises(SessionExpiredError):
        await client.get_json("/api/test")


@pytest.mark.asyncio
async def test_get_json_raises_client_error_on_404(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=404,
        json={"message": "Not Found"},
    )
    with pytest.raises(ClientError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_post_json_success(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={"ok": True},
    )
    result = await client.post_json("/api/test", json_body={"foo": "bar"})
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_session_cookie_sent_in_requests(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    fake_cookie: str,
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={},
    )
    await client.get_json("/api/test")
    request = httpx_mock.get_requests()[0]
    assert fake_cookie in request.headers.get("cookie", "")


@pytest.mark.asyncio
async def test_http_raises_server_error_on_5xx(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    """5xx 應在重試耗盡後拋出 ServerError。"""
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=500,
        json={"message": "Internal Server Error"},
    )
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=500,
        json={"message": "Internal Server Error"},
    )
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=500,
        json={"message": "Internal Server Error"},
    )
    with pytest.raises(ServerError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 500
