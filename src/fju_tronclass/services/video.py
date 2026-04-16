"""影片觀看完成度服務。

核心邏輯來自 tronclass-video-player 技能的逆向成果：
- POST /api/course/activities-read/{activityId}
- 伺服器硬上限：end - start <= 125 秒
- 建議每段 <= 90 秒留安全餘量
"""

from __future__ import annotations

from dataclasses import dataclass

from fju_tronclass.logging import get_logger
from fju_tronclass.models.activity import ActivityReadResult

logger = get_logger(__name__)

CHUNK_SIZE = 90  # 每段最大秒數，伺服器上限 125s，留安全餘量


@dataclass(frozen=True)
class VideoMarkResult:
    """批量標記影片完成的單一結果。"""

    activity_id: int
    activity_name: str
    duration: int
    completeness_pct: int
    success: bool
    error: str = ""


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


async def mark_all_videos_in_course(
    client: object,
    course_id: int,
    *,
    skip_completed: bool = True,
) -> list[VideoMarkResult]:
    """
    將指定課程中所有影片活動標記為完整觀看。

    此函式會先取得課程活動清單，篩選出 type=online_video 且有時長的活動，
    依序標記完成。

    Args:
        client: TronClassClient 實例
        course_id: 課程 ID
        skip_completed: 是否跳過已完成的影片（預設 True）

    Returns:
        每部影片的標記結果列表
    """
    activities = await client.get_course_activities(course_id)  # type: ignore[attr-defined]

    video_activities = [
        a for a in activities
        if a.is_video and a.video_duration is not None and a.video_duration > 0
    ]

    if skip_completed:
        video_activities = [a for a in video_activities if not a.is_complete]

    results: list[VideoMarkResult] = []

    for act in video_activities:
        duration = act.video_duration or 0
        try:
            last = await mark_video_complete(client, activity_id=act.id, duration=duration)
            pct = last.data.completeness if last else 0
            results.append(
                VideoMarkResult(
                    activity_id=act.id,
                    activity_name=act.display_name,
                    duration=duration,
                    completeness_pct=pct,
                    success=True,
                )
            )
        except Exception as exc:
            logger.warning(
                "標記影片失敗",
                activity_id=act.id,
                error=str(exc),
            )
            results.append(
                VideoMarkResult(
                    activity_id=act.id,
                    activity_name=act.display_name,
                    duration=duration,
                    completeness_pct=0,
                    success=False,
                    error=str(exc),
                )
            )

    logger.info(
        "批量標記完成",
        course_id=course_id,
        total=len(results),
        success=sum(1 for r in results if r.success),
        skipped=len(video_activities) - len(results),
    )
    return results
