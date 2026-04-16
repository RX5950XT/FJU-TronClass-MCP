"""影片觀看完成度服務。

核心邏輯來自 tronclass-video-player 技能的逆向成果：
- POST /api/course/activities-read/{activityId}
- 伺服器硬上限：end - start <= 125 秒
- 建議每段 <= 90 秒留安全餘量
"""

from __future__ import annotations

from fju_tronclass.logging import get_logger
from fju_tronclass.models.activity import ActivityReadResult

logger = get_logger(__name__)

CHUNK_SIZE = 90  # 每段最大秒數，伺服器上限 125s，留安全餘量


async def mark_video_complete(
    client: object,
    activity_id: int,
    duration: int,
) -> ActivityReadResult | None:
    """
    將指定活動的影片標記為完整觀看。

    自動將 duration 按 CHUNK_SIZE（90s）分段，依序呼叫
    POST /api/course/activities-read/{activityId}。

    Args:
        client: TronClassClient 實例
        activity_id: 活動 ID
        duration: 影片總時長（秒）

    Returns:
        最後一次 API 呼叫的結果；duration=0 時回傳 None。
    """
    if duration <= 0:
        logger.debug("duration 為 0，跳過標記", activity_id=activity_id)
        return None

    last_result: ActivityReadResult | None = None
    start = 0

    while start < duration:
        end = min(start + CHUNK_SIZE, duration)
        logger.debug(
            "標記影片分段",
            activity_id=activity_id,
            start=start,
            end=end,
            duration=duration,
        )
        last_result = await client.post_activity_read(  # type: ignore[attr-defined]
            activity_id,
            start=start,
            end=end,
            duration=duration,
        )
        start = end

    logger.info(
        "影片標記完成",
        activity_id=activity_id,
        duration=duration,
        completeness=last_result.data.completeness if last_result else None,
    )
    return last_result
