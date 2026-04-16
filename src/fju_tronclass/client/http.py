"""httpx AsyncClient wrapper：統一 base URL、session cookie、重試、錯誤映射。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from fju_tronclass.errors import ClientError, DownloadError, ServerError, SessionExpiredError
from fju_tronclass.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_BASE_URL = "https://elearn2.fju.edu.tw"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, ServerError)


class TronClassHttp:
    """
    不可變的 httpx.AsyncClient 包裝器。
    建好後不允許修改 session_cookie 或 base_url；需要換 cookie 時請重建實例。
    """

    def __init__(
        self,
        session_cookie: str,
        base_url: str = _DEFAULT_BASE_URL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session_cookie = session_cookie
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            cookies={"session": session_cookie},
            timeout=_DEFAULT_TIMEOUT,
            headers={
                "User-Agent": "fju-tronclass-mcp/0.1",
                "Accept": "application/json",
            },
            follow_redirects=False,
        )

    async def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """發送 GET 請求並回傳 JSON（已解析為 Python 物件）。"""
        return await self._request_with_retry("GET", path, params=params)

    async def post_json(
        self,
        path: str,
        json_body: dict[str, Any],
    ) -> Any:
        """發送 POST 請求並回傳 JSON。"""
        return await self._request_with_retry("POST", path, json_body=json_body)

    async def stream_download(self, url: str, dest: Path) -> int:
        """串流下載到 dest 路徑，回傳寫入 bytes 數。"""
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info("開始下載", url=url, dest=str(dest))
        try:
            async with self._client.stream("GET", url) as response:
                if response.status_code == 403:
                    raise DownloadError(f"下載 URL 已過期或無授權（403）：{url}")
                _raise_for_status(response)
                written = 0
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
                        written += len(chunk)
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise DownloadError(f"下載失敗：{e}") from e
        logger.info("下載完成", dest=str(dest), bytes=written)
        return written

    async def aclose(self) -> None:
        """關閉底層 HTTP 連線池。"""
        await self._client.aclose()

    async def __aenter__(self) -> TronClassHttp:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._client.request(
                method,
                path,
                params=params,
                json=json_body,
            )
        except httpx.RequestError as e:
            logger.warning("網路請求失敗", method=method, path=path, error=str(e))
            raise ServerError(0, str(e)) from e

        _raise_for_status(response)
        return response.json()


def _raise_for_status(response: httpx.Response) -> None:
    """將 HTTP 錯誤狀態碼映射為自訂例外。"""
    if response.status_code == 401:
        raise SessionExpiredError()
    if 400 <= response.status_code < 500:
        try:
            message = response.json().get("message", response.text)
        except Exception:
            message = response.text
        raise ClientError(response.status_code, message)
    if 500 <= response.status_code < 600:
        try:
            message = response.json().get("message", response.text)
        except Exception:
            message = response.text
        raise ServerError(response.status_code, message)
