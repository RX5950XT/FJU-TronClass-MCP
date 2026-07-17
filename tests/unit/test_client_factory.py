"""unit tests for mcp_server/_client_factory.py 與 cli/_helpers.py 的 cookie 回存行為。"""

from __future__ import annotations

import pytest
import pytest_httpx


@pytest.mark.asyncio
async def test_get_client_persists_rotated_cookie(
    httpx_mock: pytest_httpx.HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """伺服器 rotate cookie 後，get_client 結束時應存回 keyring。"""
    from fju_tronclass.mcp_server import _client_factory

    saved: list[str] = []
    monkeypatch.setattr(_client_factory, "load_cookie", lambda: "V2-old")
    monkeypatch.setattr(_client_factory, "save_cookie", saved.append)

    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={},
        headers={"Set-Cookie": "session=V2-new; Path=/"},
    )

    async with _client_factory.get_client() as client:
        await client._http.get_json("/api/test")

    assert saved == ["V2-new"]


@pytest.mark.asyncio
async def test_get_client_skips_save_when_cookie_unchanged(
    httpx_mock: pytest_httpx.HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cookie 沒變就不寫 keyring。"""
    from fju_tronclass.mcp_server import _client_factory

    saved: list[str] = []
    monkeypatch.setattr(_client_factory, "load_cookie", lambda: "V2-old")
    monkeypatch.setattr(_client_factory, "save_cookie", saved.append)

    httpx_mock.add_response(url="https://elearn2.fju.edu.tw/api/test", json={})

    async with _client_factory.get_client() as client:
        await client._http.get_json("/api/test")

    assert saved == []


@pytest.mark.asyncio
async def test_build_client_persists_rotated_cookie(
    httpx_mock: pytest_httpx.HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI build_client 也要在 rotate 後存回 keyring。"""
    from fju_tronclass.cli import _helpers

    saved: list[str] = []
    monkeypatch.setattr(_helpers, "load_cookie", lambda: "V2-old")
    monkeypatch.setattr(_helpers, "save_cookie", saved.append)

    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/test",
        json={},
        headers={"Set-Cookie": "session=V2-new; Path=/"},
    )

    async with _helpers.build_client() as client:
        await client._http.get_json("/api/test")

    assert saved == ["V2-new"]
