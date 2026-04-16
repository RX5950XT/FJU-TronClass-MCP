"""MCP tools：課程活動（教材清單、影片批量完成、自然語言下載）。"""

from __future__ import annotations

from fju_tronclass.mcp_server.server import mcp


@mcp.tool()
async def fju_list_course_activities(course_id: int) -> list[dict]:  # type: ignore[type-arg]
    """
    取得課程中所有學習活動的清單（教材與影片）。

    這是「自然語言下載」的第一步：先用此 tool 列出活動，
    再用 fju_search_and_download 或 fju_download_upload 下載。

    參數：
    - course_id：課程 ID（從 fju_list_courses 取得）

    回傳列表，每筆包含：
    - id：活動 ID
    - display_name：活動名稱
    - type：活動類型（"material" 教材 / "online_video" 影片）
    - is_complete：是否已完成
    - video_duration：影片時長秒數（僅 online_video 類型有值）
    - uploads：教材附件列表（僅 material 類型有值），每筆含 id/name/size
    """
    from fju_tronclass.mcp_server._client_factory import get_client

    async with get_client() as client:
        activities = await client.get_course_activities(course_id)

    return [
        {
            "id": a.id,
            "display_name": a.display_name,
            "type": a.type,
            "is_complete": a.is_complete,
            "video_duration": a.video_duration,
            "uploads": [
                {"id": u.id, "name": u.name, "size_bytes": u.size}
                for u in a.uploads
            ],
        }
        for a in activities
    ]


@mcp.tool()
async def fju_search_and_download(
    keyword: str,
    course_id: int | None = None,
    dest_dir: str | None = None,
    search_all_courses: bool = False,
) -> dict:  # type: ignore[type-arg]
    """
    依關鍵字搜尋課程教材，找到後自動下載。

    這是「自然語言下載」的核心 tool。使用者只需說檔案名稱或活動名稱的一部份，
    即可自動搜尋並下載，不需要知道 upload ID。

    範例用法：
    - 「下載資料結構課程的第三週講義」→ fju_search_and_download("第三週", course_id=101)
    - 「幫我下載所有課程中含有'排序'的教材」→ fju_search_and_download("排序", search_all_courses=True)

    參數：
    - keyword：搜尋關鍵字（可以是檔案名稱、活動名稱的片段）
    - course_id（可選）：指定搜尋的課程 ID，不填且 search_all_courses=True 則搜尋全部課程
    - dest_dir（可選）：下載目標目錄，預設 ~/Downloads/TronClass
    - search_all_courses：是否跨所有課程搜尋（會比較慢）

    回傳：
    - found：找到的 upload 數量
    - downloaded：成功下載的數量
    - results：每筆的詳細資訊（upload_name, path, size_mb, error）
    - search_results：找到但尚未下載的清單（found > downloaded 時）
    """
    from pathlib import Path

    from fju_tronclass.config import get_settings
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.downloads import download_upload
    from fju_tronclass.services.search import search_uploads_by_keyword

    settings = get_settings()
    target = Path(dest_dir) if dest_dir else settings.fjumcp_download_dir

    async with get_client() as client:
        search_results = await search_uploads_by_keyword(
            client,
            keyword=keyword,
            course_id=course_id,
            include_all_courses=search_all_courses,
        )

        if not search_results:
            return {
                "found": 0,
                "downloaded": 0,
                "results": [],
                "message": f"找不到含有「{keyword}」的教材",
            }

        download_results = []
        for sr in search_results:
            try:
                file_path, size = await download_upload(
                    client, upload_id=sr.upload_id, dest_dir=target
                )
                download_results.append(
                    {
                        "upload_id": sr.upload_id,
                        "upload_name": sr.upload_name,
                        "activity_name": sr.activity_name,
                        "course_name": sr.course_name,
                        "path": str(file_path),
                        "size_mb": round(size / 1_048_576, 2),
                        "success": True,
                        "error": None,
                    }
                )
            except Exception as exc:
                download_results.append(
                    {
                        "upload_id": sr.upload_id,
                        "upload_name": sr.upload_name,
                        "activity_name": sr.activity_name,
                        "course_name": sr.course_name,
                        "path": None,
                        "size_mb": 0,
                        "success": False,
                        "error": str(exc),
                    }
                )

    success_count = sum(1 for r in download_results if r["success"])
    return {
        "found": len(search_results),
        "downloaded": success_count,
        "results": download_results,
        "message": f"找到 {len(search_results)} 個檔案，成功下載 {success_count} 個",
    }


@mcp.tool()
async def fju_batch_mark_videos_complete(
    course_id: int,
    skip_completed: bool = True,
) -> dict:  # type: ignore[type-arg]
    """
    將指定課程中所有影片活動一次標記為完整觀看。

    此 tool 會自動取得課程所有影片活動，依序標記完成，
    不需要逐一提供 activity_id 和 duration。

    使用者須自行評估是否符合課程規範及學業誠信要求。
    此操作繞過觀看驗證，只增加完成度，不增加學習時數。

    參數：
    - course_id：課程 ID（從 fju_list_courses 取得）
    - skip_completed：是否跳過已完成的影片（預設 True，避免重複標記）

    回傳：
    - total：處理的影片數量
    - success：成功標記的數量
    - skipped：跳過（已完成）的數量
    - results：每部影片的詳細結果
    """
    from fju_tronclass.mcp_server._client_factory import get_client
    from fju_tronclass.services.video import mark_all_videos_in_course

    async with get_client() as client:
        results = await mark_all_videos_in_course(
            client, course_id=course_id, skip_completed=skip_completed
        )

    success_count = sum(1 for r in results if r.success)
    return {
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": [
            {
                "activity_id": r.activity_id,
                "activity_name": r.activity_name,
                "duration_seconds": r.duration,
                "completeness_pct": r.completeness_pct,
                "success": r.success,
                "error": r.error or None,
            }
            for r in results
        ],
        "message": f"共 {len(results)} 部影片，成功標記 {success_count} 部",
    }
