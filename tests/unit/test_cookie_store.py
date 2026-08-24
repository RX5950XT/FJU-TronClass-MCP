"""unit tests for auth/cookie_store.py 與 auth/session.py。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_httpx

from fju_tronclass.errors import AuthError


@pytest.fixture
def cookie_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_parse_cookie_expiry() -> None:
    from fju_tronclass.auth.cookie_store import parse_cookie_expiry

    cookie = "V2-1-aaaa.NDkyOTAy.1787634124104.sig"
    expiry = parse_cookie_expiry(cookie)
    assert expiry == datetime.fromtimestamp(1787634124104 / 1000, tz=UTC)
    assert parse_cookie_expiry("not-a-cookie") is None
    assert parse_cookie_expiry("V2-1-aaaa.bbb.notdigits.sig") is None


def test_file_roundtrip_when_keyring_unavailable(
    cookie_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fju_tronclass.auth import cookie_store

    monkeypatch.setattr(cookie_store, "_keyring_get", lambda: None)
    monkeypatch.setattr(cookie_store, "_keyring_set", lambda _c: False)
    monkeypatch.setattr(cookie_store, "_keyring_delete", lambda: None)

    cookie_store.save_cookie("V2-file-cookie")
    path = cookie_store.cookie_file_path()
    assert path.is_file()
    assert path.read_text(encoding="utf-8") == "V2-file-cookie"
    assert cookie_store.load_cookie() == "V2-file-cookie"

    cookie_store.delete_cookie()
    assert not path.exists()
    with pytest.raises(AuthError):
        cookie_store.load_cookie()


def test_load_prefers_keyring_over_file(
    cookie_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fju_tronclass.auth import cookie_store

    cookie_store._write_file("V2-file")
    monkeypatch.setattr(cookie_store, "_keyring_get", lambda: "V2-keyring")
    assert cookie_store.load_cookie() == "V2-keyring"


def test_persist_if_rotated(cookie_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fju_tronclass.auth import cookie_store

    saved: list[str] = []
    monkeypatch.setattr(cookie_store, "save_cookie", saved.append)
    assert cookie_store.persist_if_rotated("V2-old", "V2-new") is True
    assert cookie_store.persist_if_rotated("V2-old", "V2-old") is False
    assert cookie_store.persist_if_rotated("V2-old", "") is False
    assert saved == ["V2-new"]


@pytest.mark.asyncio
async def test_verify_and_persist_saves_rotated_cookie(
    cookie_dir: Path,
    httpx_mock: pytest_httpx.HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fju_tronclass.auth import session as session_mod

    saved: list[str] = []
    monkeypatch.setattr(session_mod, "save_cookie", saved.append)
    monkeypatch.setattr(session_mod, "persist_if_rotated", lambda o, c: saved.append(c) or True)

    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/my-courses?page=1&page_size=1",
        json={"courses": [], "total": 7, "page": 1, "page_size": 1},
        headers={"Set-Cookie": "session=V2-rotated; Path=/"},
    )

    count = await session_mod.verify_and_persist("V2-old", "https://elearn2.fju.edu.tw")
    assert count == 7
    assert saved == ["V2-rotated"]


@pytest.mark.asyncio
async def test_verify_and_persist_always_save_on_login(
    cookie_dir: Path,
    httpx_mock: pytest_httpx.HTTPXMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fju_tronclass.auth import session as session_mod

    saved: list[str] = []
    monkeypatch.setattr(session_mod, "save_cookie", saved.append)

    httpx_mock.add_response(
        url="https://elearn2.fju.edu.tw/api/my-courses?page=1&page_size=1",
        json={"courses": [], "total": 3, "page": 1, "page_size": 1},
    )

    count = await session_mod.verify_and_persist(
        "V2-first", "https://elearn2.fju.edu.tw", always_save=True
    )
    assert count == 3
    assert saved == ["V2-first"]
