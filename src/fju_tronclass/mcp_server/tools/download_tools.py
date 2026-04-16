"""MCP tools：教材下載。"""

from __future__ import annotations

from pathlib import Path

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_get_upload_info(upload_id: int) -> dict:  # type: ignore[type-arg]
    """
    取得 upload（課程教材）的詳細資訊。

    參數：
    - upload_id：Upload ID

    回傳：id、name（原始檔名）、size（bytes）、
    allow_download（UI 層設定，不影響 API 下載能力）、created_at
    """
    from fju_tronclass.mcp_server._client_factory import get_client

    async with get_client() as client:
        meta = await client.get_upload_meta(upload_id)

    return meta.model_dump(mode="json")


@mcp.tool()
async def fju_download_upload(upload_id: int, dest_dir: str | None = None) -> dict:  # type: ignore[type-arg]
    """
    下載指定的課程教材到本機。

    即使課程設定為「不允許下載」，API 層仍會提供有效的下載 URL，
    此 tool 利用此機制直接下載。下載的檔案僅供本人學習使用，請勿散佈。

    參數：
    - upload_id：Upload ID（從課程頁面 URL 或活動 API 取得）
    - dest_dir（可選）：下載目標目錄，預設為 ~/Downloads/TronClass

    回傳：
    - path：本機檔案完整路徑
    - filename：檔案名稱
    - size_bytes：檔案大小
    - size_mb：檔案大小（MB）
    """
    from fju_tronclass.config import get_settings
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.downloads import download_upload

    settings = get_settings()
    target = Path(dest_dir) if dest_dir else settings.fjumcp_download_dir

    async with get_client() as client:
        file_path, size = await download_upload(client, upload_id=upload_id, dest_dir=target)

    return {
        "path": str(file_path),
        "filename": file_path.name,
        "size_bytes": size,
        "size_mb": round(size / 1_048_576, 2),
    }
