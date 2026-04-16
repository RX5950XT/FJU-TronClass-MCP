"""搜尋服務：在課程活動與教材中按關鍵字搜尋可下載的 upload。

讓 Claude 可以自然語言操作：
  「幫我下載第三週講義」→ search_uploads_by_keyword(client, "第三週", course_id=101)
  → 找到 upload_id → fju_download_upload(upload_id)
"""

from __future__ import annotations

from dataclasses import dataclass

from fju_tronclass.logging import get_logger
from fju_tronclass.models.activity import Activity

logger = get_logger(__name__)


@dataclass(frozen=True)
class UploadSearchResult:
    """搜尋到的 upload 項目。"""

    upload_id: int
    upload_name: str
    upload_size: int
    activity_id: int
    activity_name: str
    course_id: int
    course_name: str
    activity_type: str  # "material" or "online_video"


async def search_uploads_by_keyword(
    client: object,
    keyword: str,
    course_id: int | None = None,
    *,
    include_all_courses: bool = False,
) -> list[UploadSearchResult]:
    """
    在指定課程（或所有課程）的活動教材中，依關鍵字搜尋可下載的 upload。

    搜尋範圍：
    - 活動名稱（title / name）
    - upload 檔案名稱（name）

    Args:
        client: TronClassClient 實例
        keyword: 搜尋關鍵字（不區分大小寫）
        course_id: 指定課程 ID；若為 None 且 include_all_courses=True 則搜尋全部課程
        include_all_courses: 是否跨所有課程搜尋（耗時較長）

    Returns:
        符合條件的 UploadSearchResult 列表，按課程 ID 和活動 ID 排序
    """
    kw_lower = keyword.lower().strip()
    results: list[UploadSearchResult] = []

    if course_id is not None:
        courses = [(course_id, "")]
    elif include_all_courses:
        all_courses = await client.get_my_courses()  # type: ignore[attr-defined]
        courses = [(c.id, c.name) for c in all_courses]
    else:
        raise ValueError(
            "必須提供 course_id，或設定 include_all_courses=True 搜尋全部課程"
        )

    for cid, cname in courses:
        try:
            activities = await client.get_course_activities(cid)  # type: ignore[attr-defined]
        except Exception:
            logger.warning("無法取得課程活動清單", course_id=cid)
            continue

        for act in activities:
            results.extend(
                _match_activity(act, kw_lower, cid, cname)
            )

    results.sort(key=lambda r: (r.course_id, r.activity_id))
    logger.info(
        "搜尋完成",
        keyword=keyword,
        result_count=len(results),
    )
    return results


def _match_activity(
    act: Activity,
    kw_lower: str,
    course_id: int,
    course_name: str,
) -> list[UploadSearchResult]:
    """從單一 Activity 中篩選符合關鍵字的 uploads。"""
    if not act.uploads:
        return []

    act_name_lower = act.display_name.lower()
    matched: list[UploadSearchResult] = []

    for upload in act.uploads:
        upload_name_lower = upload.name.lower()
        # 活動名稱或 upload 檔名有任一包含關鍵字即符合
        if kw_lower in act_name_lower or kw_lower in upload_name_lower:
            matched.append(
                UploadSearchResult(
                    upload_id=upload.id,
                    upload_name=upload.name,
                    upload_size=upload.size,
                    activity_id=act.id,
                    activity_name=act.display_name,
                    course_id=course_id,
                    course_name=course_name,
                    activity_type=act.type,
                )
            )

    return matched
