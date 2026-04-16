"""unit tests for services/downloads.py"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from fju_tronclass.models.upload import UploadMeta, UploadUrl


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock()
    client.get_upload_meta.return_value = UploadMeta(
        id=30001,
        name="第三週講義.pdf",
        size=2048576,
        allow_download=False,
    )
    client.get_upload_url.return_value = UploadUrl(
        url="https://media.example.com/file/abc?token=xyz"
    )
    client._http = AsyncMock()
    client._http.stream_download = AsyncMock(return_value=2048576)
    return client


@pytest.mark.asyncio
async def test_download_upload_calls_correct_methods(
    mock_client: AsyncMock,
    tmp_path: Path,
) -> None:
    from fju_tronclass.services.downloads import download_upload

    path, size = await download_upload(mock_client, upload_id=30001, dest_dir=tmp_path)

    mock_client.get_upload_meta.assert_called_once_with(30001)
    mock_client.get_upload_url.assert_called_once_with(30001)
    mock_client._http.stream_download.assert_called_once()
    assert size == 2048576


@pytest.mark.asyncio
async def test_download_upload_returns_correct_path(
    mock_client: AsyncMock,
    tmp_path: Path,
) -> None:
    from fju_tronclass.services.downloads import download_upload

    path, _ = await download_upload(mock_client, upload_id=30001, dest_dir=tmp_path)
    assert path == tmp_path / "第三週講義.pdf"


@pytest.mark.parametrize(
    "input_name, expected",
    [
        ("正常檔名.pdf", "正常檔名.pdf"),
        ('含<>:"/\\|?*的檔名.pdf', "含_________的檔名.pdf"),
        ("a" * 250 + ".pdf", "a" * 196 + ".pdf"),  # 截斷至 200 字（含副檔名 4 字）
        ("  空白前後  .pdf", "空白前後.pdf"),
        ("Makefile", "Makefile"),               # 無副檔名（dot_idx <= 0）
        (".gitignore", ".gitignore"),           # 以點開頭，dot_idx == 0 → 無副檔名分支
    ],
)
def test_safe_filename(input_name: str, expected: str) -> None:
    from fju_tronclass.services.downloads import _safe_filename

    assert _safe_filename(input_name) == expected
