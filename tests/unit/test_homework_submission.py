"""services/homework.py 作業草稿上傳流程測試（mock client）。"""

from __future__ import annotations

from typing import Any

import pytest

from fju_tronclass.services.homework import (
    find_draft_submission,
    list_my_submissions,
    upload_homework_draft,
    wait_upload_ready,
)


class FakeProfile:
    id = 492902


class FakeUploadMeta:
    def __init__(self, status: str) -> None:
        self.status = status


class FakeClient:
    """最小 mock：涵蓋 upload_homework_draft 觸及的所有 client 方法。"""

    def __init__(
        self,
        submissions: list[dict[str, Any]] | None = None,
        statuses: list[str] | None = None,
    ) -> None:
        self._submissions = submissions or []
        self._statuses = statuses or ["ready"]
        self.create_upload_calls: list[dict[str, Any]] = []
        self.put_calls: list[dict[str, Any]] = []
        self.saved_bodies: list[dict[str, Any]] = []
        self.meta_polls = 0

    async def get_profile(self) -> FakeProfile:
        return FakeProfile()

    async def get_student_submission_list(
        self, activity_id: int, student_id: int
    ) -> list[dict[str, Any]]:
        assert student_id == 492902
        return self._submissions

    async def create_upload(self, name: str, size: int, parent_id: int = 0) -> dict[str, Any]:
        self.create_upload_calls.append({"name": name, "size": size})
        return {
            "id": 36861496,
            "upload_url": "https://mediaelearn2.fju.edu.tw/upload/file/36861496?token=x",
            "storage_type": "MEDIA",
        }

    async def put_upload_file(
        self, upload_url: str, file_path: Any, content_type: str = "application/octet-stream"
    ) -> dict[str, Any]:
        self.put_calls.append({"url": upload_url, "ctype": content_type})
        return {"file_key": "abc"}

    async def get_upload_meta(self, upload_id: int) -> FakeUploadMeta:
        self.meta_polls += 1
        status = self._statuses[min(self.meta_polls - 1, len(self._statuses) - 1)]
        return FakeUploadMeta(status)

    async def save_homework_submission(
        self, activity_id: int, **kwargs: Any
    ) -> dict[str, Any]:
        self.saved_bodies.append(kwargs)
        return {"submission": {"id": 22645651}}


@pytest.mark.asyncio
async def test_find_draft_submission_picks_latest_draft() -> None:
    client = FakeClient(
        submissions=[
            {"id": 1, "is_draft": False, "marked_submitted": True},
            {"id": 2, "is_draft": True, "submitted_at": "2026-09-22T07:00:00Z"},
            {"id": 3, "is_draft": True, "submitted_at": "2026-09-22T07:30:00Z"},
            {"id": 4, "is_draft": True, "is_redo": True, "submitted_at": "2026-09-22T08:00:00Z"},
        ]
    )
    draft = await find_draft_submission(client, 3136555, 492902)
    assert draft is not None
    assert draft["id"] == 3  # 最新且非 redo 的草稿


@pytest.mark.asyncio
async def test_find_draft_submission_none_when_only_submitted() -> None:
    client = FakeClient(submissions=[{"id": 1, "is_draft": False}])
    assert await find_draft_submission(client, 3136555, 492902) is None


@pytest.mark.asyncio
async def test_wait_upload_ready_immediate() -> None:
    client = FakeClient(statuses=["ready"])
    await wait_upload_ready(client, 1, interval=0.01, timeout=1.0)
    assert client.meta_polls == 1


@pytest.mark.asyncio
async def test_wait_upload_ready_retries_until_ready() -> None:
    client = FakeClient(statuses=["processing", "processing", "ready"])
    await wait_upload_ready(client, 1, interval=0.01, timeout=5.0)
    assert client.meta_polls == 3


@pytest.mark.asyncio
async def test_wait_upload_ready_raises_on_failed() -> None:
    client = FakeClient(statuses=["failed"])
    with pytest.raises(RuntimeError, match="轉檔失敗"):
        await wait_upload_ready(client, 1, interval=0.01, timeout=1.0)


@pytest.mark.asyncio
async def test_wait_upload_ready_timeout() -> None:
    client = FakeClient(statuses=["processing"])
    with pytest.raises(TimeoutError):
        await wait_upload_ready(client, 1, interval=0.01, timeout=0.05)


@pytest.mark.asyncio
async def test_upload_homework_draft_creates_new_draft(tmp_path: Any) -> None:
    f = tmp_path / "HW1.jpg"
    f.write_bytes(b"\xff\xd8fakejpeg")
    client = FakeClient(submissions=[])  # 無既有草稿

    result = await upload_homework_draft(client, 3136555, f, poll_interval=0.01)

    assert result["draft_updated"] is False
    assert result["upload_id"] == 36861496
    assert result["upload_name"] == "HW1.jpg"
    assert client.create_upload_calls == [{"name": "HW1.jpg", "size": 10}]
    assert client.put_calls and "mediaelearn2" in client.put_calls[0]["url"]
    assert client.put_calls[0]["ctype"] == "image/jpeg"
    # 新草稿 → POST（submission_id 不存在）
    assert len(client.saved_bodies) == 1
    body = client.saved_bodies[0]
    assert body["is_draft"] is True
    assert body["upload_ids"] == [36861496]
    assert body.get("submission_id") is None


@pytest.mark.asyncio
async def test_upload_homework_draft_updates_existing(tmp_path: Any) -> None:
    f = tmp_path / "HW1.jpg"
    f.write_bytes(b"data")
    client = FakeClient(
        submissions=[{"id": 22645000, "is_draft": True, "submitted_at": "2026-09-22T06:00:00Z"}]
    )

    result = await upload_homework_draft(client, 3136555, f, poll_interval=0.01)

    assert result["draft_updated"] is True
    body = client.saved_bodies[0]
    assert body["submission_id"] == 22645000  # 既有草稿 → 帶 submission_id（PUT 更新）


@pytest.mark.asyncio
async def test_upload_homework_draft_missing_file(tmp_path: Any) -> None:
    client = FakeClient()
    with pytest.raises(FileNotFoundError):
        await upload_homework_draft(client, 3136555, tmp_path / "nope.jpg")


@pytest.mark.asyncio
async def test_list_my_submissions_uses_profile_id() -> None:
    client = FakeClient(submissions=[{"id": 9, "is_draft": True}])
    items = await list_my_submissions(client, 3136555)
    assert items == [{"id": 9, "is_draft": True}]
