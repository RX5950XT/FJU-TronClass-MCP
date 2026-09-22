"""作業繳交（草稿）服務。

流程於 2026-09-22 以相對論 HW#1 全程實測驗證：

1. ``POST /api/uploads``（preUpload）取得 upload id 與 upload_url
2. multipart ``PUT`` 檔案本體到 upload_url（外部媒體主機，不需 session）
3. 輪詢 ``GET /api/uploads/{id}`` 直到 ``status == "ready"``
4. ``POST /api/course/activities/{aid}/submissions``（is_draft=true）存草稿；
   若已有草稿則同 endpoint 改 PUT 並帶 ``submission_id``

安全設計：本服務只會寫入草稿（is_draft=True），正式繳交一律由本人於網頁操作。
"""

from __future__ import annotations

import asyncio
import mimetypes
import time
from pathlib import Path
from typing import Any

from fju_tronclass.logging import get_logger

logger = get_logger(__name__)


def guess_content_type(path: Path) -> str:
    """依副檔名猜 content-type，猜不到用 octet-stream。"""
    guessed = mimetypes.guess_type(path.name)[0]
    return guessed or "application/octet-stream"


async def wait_upload_ready(
    client: Any,
    upload_id: int,
    *,
    interval: float = 3.0,
    timeout: float = 120.0,
) -> None:
    """輪詢 upload 狀態直到 ready；逾時或 failed 就丟錯。"""
    deadline = time.monotonic() + timeout
    while True:
        meta = await client.get_upload_meta(upload_id)
        status = (meta.status or "").lower()
        if status == "ready":
            return
        if status in {"failed", "error"}:
            raise RuntimeError(f"upload {upload_id} 轉檔失敗（status={status}）")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"upload {upload_id} 遲遲未 ready（超過 {timeout:.0f} 秒，status={status or '未知'}）。"
                "可稍後用 homework submissions 確認狀態。"
            )
        await asyncio.sleep(interval)


async def find_draft_submission(
    client: Any,
    activity_id: int,
    student_id: int,
) -> dict[str, Any] | None:
    """找出自己最新的草稿 submission（is_draft=True 且非重做版）。"""
    items = await client.get_student_submission_list(activity_id, student_id)
    drafts = [
        s
        for s in items
        if s.get("is_draft") and not s.get("is_redo") and s.get("id")
    ]
    if not drafts:
        return None
    # 取最新一筆（submitted_at/created_at 降序，缺欄位就保持原順序取第一筆）
    def _key(s: dict[str, Any]) -> str:
        return str(s.get("submitted_at") or s.get("created_at") or "")

    latest: dict[str, Any] = max(drafts, key=_key)
    return latest


async def upload_homework_draft(
    client: Any,
    activity_id: int,
    file_path: Path,
    *,
    comment: str = "",
    poll_interval: float = 3.0,
    poll_timeout: float = 120.0,
) -> dict[str, Any]:
    """
    上傳檔案並寫入作業草稿（只存草稿，不正式繳交）。

    回傳 dict：submission_id（草稿 id）、upload_id、draft_updated（是否更新既有草稿）。
    """
    file_path = file_path.expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"找不到檔案：{file_path}")

    profile = await client.get_profile()
    student_id = profile.id

    existing = await find_draft_submission(client, activity_id, student_id)
    draft_id = existing["id"] if existing else None

    size = file_path.stat().st_size
    created = await client.create_upload(file_path.name, size)
    upload_id = int(created["id"])
    upload_url = str(created["upload_url"])
    logger.info(
        "preUpload 完成", upload_id=upload_id, storage=created.get("storage_type")
    )

    await client.put_upload_file(
        upload_url, file_path, content_type=guess_content_type(file_path)
    )

    await wait_upload_ready(
        client, upload_id, interval=poll_interval, timeout=poll_timeout
    )

    result = await client.save_homework_submission(
        activity_id,
        comment=comment,
        upload_ids=[upload_id],
        is_draft=True,
        submission_id=draft_id,
    )
    saved = result.get("submission") if isinstance(result, dict) else None
    submission_id = None
    if isinstance(saved, dict):
        submission_id = saved.get("id")
    logger.info(
        "草稿已儲存",
        activity_id=activity_id,
        draft_id=draft_id,
        submission_id=submission_id,
        upload_id=upload_id,
    )
    return {
        "activity_id": activity_id,
        "submission_id": submission_id,
        "draft_updated": draft_id is not None,
        "upload_id": upload_id,
        "upload_name": file_path.name,
        "upload_size": size,
    }


async def list_my_submissions(
    client: Any,
    activity_id: int,
) -> list[dict[str, Any]]:
    """列出本人於某作業的繳交記錄（含草稿）。"""
    profile = await client.get_profile()
    items: list[dict[str, Any]] = await client.get_student_submission_list(
        activity_id, profile.id
    )
    return items
