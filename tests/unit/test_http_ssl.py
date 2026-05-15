from __future__ import annotations

import ssl
from unittest.mock import patch


def test_http_client_uses_ssl_context(fake_cookie: str, base_url: str) -> None:
    from fju_tronclass.client.http import TronClassHttp

    captured: dict[str, object] = {}

    def _fake_async_client(*args: object, **kwargs: object) -> object:
        captured.update(kwargs)

        class _Client:
            async def aclose(self) -> None:
                return None

        return _Client()

    with patch("fju_tronclass.client.http.httpx.AsyncClient", side_effect=_fake_async_client):
        TronClassHttp(session_cookie=fake_cookie, base_url=base_url)

    assert isinstance(captured["verify"], ssl.SSLContext)
