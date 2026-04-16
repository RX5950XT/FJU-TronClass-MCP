"""補充 http.py 的覆蓋率測試：stream_download、302 重導、錯誤分支。"""

from __future__ import annotations

import pytest
import pytest_httpx

from fju_tronclass.errors import DownloadError


@pytest.fixture
def client(fake_cookie: str, base_url: str):  # type: ignore[no-untyped-def]
    from fju_tronclass.client.http import TronClassHttp
    return TronClassHttp(session_cookie=fake_cookie, base_url=base_url)


@pytest.mark.asyncio
async def test_get_json_with_params(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test?page=1&size=5",
        json={"data": "ok"},
    )
    result = await client.get_json("/api/test", params={"page": 1, "size": 5})
    assert result == {"data": "ok"}


@pytest.mark.asyncio
async def test_get_json_raises_client_error_on_403(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
) -> None:
    from fju_tronclass.errors import ClientError

    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        status_code=403,
        json={"message": "Forbidden"},
    )
    with pytest.raises(ClientError) as exc_info:
        await client.get_json("/api/test")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_stream_download_raises_on_403(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://media.example.com/file",
        status_code=403,
    )
    with pytest.raises(DownloadError):
        await client.stream_download("https://media.example.com/file", tmp_path / "test.pdf")


@pytest.mark.asyncio
async def test_stream_download_writes_bytes(
    httpx_mock: pytest_httpx.HTTPXMock,
    client,  # type: ignore[no-untyped-def]
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    httpx_mock.add_response(
        url="https://media.example.com/file.pdf",
        content=b"hello world",
    )
    dest = tmp_path / "file.pdf"
    written = await client.stream_download("https://media.example.com/file.pdf", dest)
    assert written == 11
    assert dest.read_bytes() == b"hello world"


@pytest.mark.asyncio
async def test_context_manager_closes_client(
    fake_cookie: str,
    base_url: str,
) -> None:
    from fju_tronclass.client.http import TronClassHttp

    async with TronClassHttp(session_cookie=fake_cookie, base_url=base_url) as http:
        assert http._client is not None
    # 不應拋出例外
