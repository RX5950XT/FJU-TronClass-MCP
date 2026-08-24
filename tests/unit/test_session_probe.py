from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from fju_tronclass.errors import ServerError, SessionExpiredError


@pytest.mark.asyncio
async def test_probe_session_returns_course_count() -> None:
    from fju_tronclass.auth.session_probe import probe_session

    mocked_client = AsyncMock()
    page = AsyncMock()
    page.total = 12
    mocked_client.get_my_courses_page.return_value = page

    with patch("fju_tronclass.client.tronclass.TronClassClient", return_value=mocked_client):
        count = await probe_session(object())

    assert count == 12


@pytest.mark.asyncio
async def test_probe_session_preserves_session_expired_error() -> None:
    from fju_tronclass.auth.session_probe import probe_session

    mocked_client = AsyncMock()
    mocked_client.get_my_courses_page.side_effect = SessionExpiredError()

    with (
        patch("fju_tronclass.client.tronclass.TronClassClient", return_value=mocked_client),
        pytest.raises(SessionExpiredError),
    ):
        await probe_session(object())


@pytest.mark.asyncio
async def test_probe_session_does_not_mask_server_error() -> None:
    from fju_tronclass.auth.session_probe import probe_session

    mocked_client = AsyncMock()
    mocked_client.get_my_courses_page.side_effect = ServerError(0, "TLS verify failed")

    with (
        patch("fju_tronclass.client.tronclass.TronClassClient", return_value=mocked_client),
        pytest.raises(ServerError, match="TLS verify failed"),
    ):
        await probe_session(object())
