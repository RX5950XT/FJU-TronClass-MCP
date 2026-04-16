"""unit tests for services/video.py — 重點驗證 90s 分段邏輯與 125s 上限。"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from fju_tronclass.models.activity import ActivityReadRanges, ActivityReadResult


def _make_result(completeness: int = 100) -> ActivityReadResult:
    return ActivityReadResult(
        completeness="full",
        data=ActivityReadRanges(completeness=completeness, ranges=[]),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "duration, expected_calls",
    [
        (0, 0),       # 0 秒無需呼叫
        (30, 1),      # 短影片一段
        (90, 1),      # 恰好 90s
        (91, 2),      # 90 + 1
        (125, 2),     # 90 + 35
        (177, 2),     # 90 + 87
        (180, 2),     # 90 + 90
        (181, 3),     # 90 + 90 + 1
        (1000, 12),   # 11*90 + 10 = 12 段
    ],
)
async def test_chunking_call_count(duration: int, expected_calls: int) -> None:
    from fju_tronclass.services.video import mark_video_complete

    mock_client = AsyncMock()
    mock_client.post_activity_read.return_value = _make_result()

    await mark_video_complete(mock_client, activity_id=99, duration=duration)

    assert mock_client.post_activity_read.call_count == expected_calls


@pytest.mark.asyncio
@pytest.mark.parametrize("duration", [30, 90, 91, 125, 177, 1000])
async def test_each_chunk_within_90s(duration: int) -> None:
    """每一次 post_activity_read 呼叫的 end-start 都不得超過 90 秒。"""
    from fju_tronclass.services.video import mark_video_complete

    mock_client = AsyncMock()
    mock_client.post_activity_read.return_value = _make_result()

    await mark_video_complete(mock_client, activity_id=99, duration=duration)

    for c in mock_client.post_activity_read.call_args_list:
        start = c.kwargs.get("start", c.args[1] if len(c.args) > 1 else None)
        end = c.kwargs.get("end", c.args[2] if len(c.args) > 2 else None)
        if start is not None and end is not None:
            assert end - start <= 90, f"chunk too large: start={start} end={end}"


@pytest.mark.asyncio
async def test_chunks_cover_full_duration() -> None:
    """所有 chunk 合起來應完整覆蓋 [0, duration]。"""
    from fju_tronclass.services.video import mark_video_complete

    duration = 177
    mock_client = AsyncMock()
    mock_client.post_activity_read.return_value = _make_result()

    await mark_video_complete(mock_client, activity_id=99, duration=duration)

    calls = mock_client.post_activity_read.call_args_list
    # 取出 start/end 組（支援 keyword 或 positional）
    segments = []
    for c in calls:
        kw = c.kwargs
        args = c.args
        s = kw.get("start", args[1] if len(args) > 1 else None)
        e = kw.get("end", args[2] if len(args) > 2 else None)
        segments.append((s, e))

    assert segments[0][0] == 0
    assert segments[-1][1] == duration
    # 連續性：每段的 end 等於下一段的 start
    for (_, e), (s2, _) in zip(segments, segments[1:], strict=False):
        assert e == s2


@pytest.mark.asyncio
async def test_zero_duration_returns_none() -> None:
    """duration=0 應直接回傳 None（無需呼叫 API）。"""
    from fju_tronclass.services.video import mark_video_complete

    mock_client = AsyncMock()
    result = await mark_video_complete(mock_client, activity_id=99, duration=0)
    assert result is None
    mock_client.post_activity_read.assert_not_called()
