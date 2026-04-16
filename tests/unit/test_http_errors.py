"""補充 http.py 覆蓋率：非 JSON 4xx/5xx body、RequestError、stream download RequestError。"""

from __future__ import annotations

import pytest
import pytest_httpx

from fju_tronclass.errors import ClientError, DownloadError, ServerError


@pytest.fixture
def client(fake_cookie: str, base_url: str):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.http import TronClassHttp
    return TronClassHttp(session_cookie=fake_cookie, base_url=base_url)


@pytest.mark.asyncio
async def test_client_error_with_non_json_body(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    """4xx 非 JSON body 應使用 response.text 作為訊息。"""
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=422,
        content=b"Unprocessable Entity",
        headers={"Content-Type": "text/plain"},
    )
    with pytest.raises(ClientError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 422
    assert "Unprocessable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_server_error_with_non_json_body(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    """5xx 非 JSON body 應使用 response.text 作為訊息。"""
    for _ in range(3):
        httpx_mock.add_response(
            url="https://elearn2.fju.edu.tw/api/test",
            status_code=503,
            content=b"Service Unavailable",
            headers={"Content-Type": "text/plain"},
        )
    with pytest.raises(ServerError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_request_error_raises_server_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    """網路層 RequestError（如 DNS 失敗）應包裝為 ServerError(0, ...)。"""
    import httpx as _httpx

    httpx_mock.add_exception(
        _httpx.ConnectError("Connection refused"),
        url="https://elearn2.fju.edu.tw/api/test",
    )
    httpx_mock.add_exception(
        _httpx.ConnectError("Connection refused"),
        url="https://elearn2.fju.edu.tw/api/test",
    )
    httpx_mock.add_exception(
        _httpx.ConnectError("Connection refused"),
        url="https://elearn2.fju.edu.tw/api/test",
    )
    with pytest.raises(ServerError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 0


@pytest.mark.asyncio
async def test_stream_download_request_error(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """stream_download 遇到 RequestError 時應包裝為 DownloadError。"""
    import httpx as _httpx

    httpx_mock.add_exception(
        _httpx.ConnectError("Connection refused"),
        url="https://media.example.com/file.pdf",
    )
    with pytest.raises(DownloadError):
        await client.stream_download(
            "https://media.example.com/file.pdf", tmp_path / "file.pdf"
        )
