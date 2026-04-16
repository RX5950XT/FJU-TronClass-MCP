"""教材下載服務。

核心邏輯來自 tronclass-downloader 技能的逆向成果：
- GET /api/uploads/{id}/url → 即使 allow_download=false 仍回傳有效 URL
- 下載到本機後，URL 含臨時 token 不對外分享
"""

from __future__ import annotations

import re
from pathlib import Path

from fju_tronclass.logging import get_logger

logger = get_logger(__name__)

_ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|?*]')
_MAX_FILENAME_LEN = 200


def _safe_filename(name: str) -> str:
    """
    移除 Windows 非法字元，截斷至 MAX_FILENAME_LEN 字，去除前後空白（含 stem 末尾）。
    非法字元以底線替換，保留副檔名完整性。

    使用 rfind('.') 而非 pathlib.Path，避免 Windows 上 / 和 \\ 被誤解為路徑分隔符。
    """
    name = name.strip()
    dot_idx = name.rfind(".")
    if dot_idx > 0:
        stem = name[:dot_idx].strip()
        suffix = name[dot_idx:]
    else:
        stem = name
        suffix = ""

    clean_stem = _ILLEGAL_CHARS_RE.sub("_", stem)
    clean_suffix = _ILLEGAL_CHARS_RE.sub("_", suffix)
    result = clean_stem + clean_suffix

    if len(result) > _MAX_FILENAME_LEN:
        truncated_stem = clean_stem[: _MAX_FILENAME_LEN - len(clean_suffix)]
        result = truncated_stem + clean_suffix

    return result


async def download_upload(
    client: object,
    upload_id: int,
    dest_dir: Path,
) -> tuple[Path, int]:
    """
    下載指定 upload 到 dest_dir，回傳 (本機路徑, 檔案大小 bytes)。

    即使 allow_download=false，API 仍會回傳有效下載 URL（tronclass-downloader 技能已驗證）。
    下載後的檔案僅供本人學習使用，請勿散佈。

    Args:
        client: TronClassClient 實例
        upload_id: Upload ID（從課程頁面或 API 取得）
        dest_dir: 下載目標目錄

    Returns:
        (下載後的完整路徑, 檔案大小 bytes)
    """
    meta = await client.get_upload_meta(upload_id)  # type: ignore[attr-defined]
    url_info = await client.get_upload_url(upload_id)  # type: ignore[attr-defined]

    safe_name = _safe_filename(meta.name)
    dest = dest_dir / safe_name

    logger.info(
        "開始下載教材",
        upload_id=upload_id,
        name=meta.name,
        size=meta.size,
        allow_download=meta.allow_download,
    )

    size = await client._http.stream_download(url_info.url, dest)  # type: ignore[attr-defined]

    return dest, size
