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


@pytest.mark.asyncio
async def test_session_cookie_property_tracks_rotation(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    fake_cookie: str,
) -> None:
    """伺服器 rotate session cookie 時，property 應回傳最新值。"""
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={},
        headers={"Set-Cookie": "session=V2-rotated-cookie; Path=/"},
    )
    assert client.session_cookie == fake_cookie
    await client.get_json("/api/test")
    assert client.session_cookie == "V2-rotated-cookie"


@pytest.mark.asyncio
async def test_get_json_raises_session_expired_on_login_redirect(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    """API 被 302 導向登入頁時應判定為 session 過期，而非拋出 JSON 解析錯誤。"""
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=302,
        headers={"Location": "https://elearn2.fju.edu.tw/login"},
    )
    with pytest.raises(SessionExpiredError):
        await client.get_json("/api/test")


@pytest.mark.asyncio
async def test_stream_download_follows_redirect(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """下載 URL 302 導向 CDN 時應跟隨 redirect 取得實際內容。"""
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/files/1",
        status_code=302,
        headers={"Location": "https://cdn.example.com/real-file"},
    )
    httpx_mock.add_response(
        url="https://cdn.example.com/real-file",
        content=b"file-content",
    )
    dest = tmp_path / "out.bin"
    written = await client.stream_download("https://elearn2.fju.edu.tw/files/1", dest)
    assert written == len(b"file-content")
    assert dest.read_bytes() == b"file-content"
    # session cookie 不應洩漏到外部 CDN
    cdn_request = httpx_mock.get_requests()[-1]
    assert "session" not in cdn_request.headers.get("cookie", "")
