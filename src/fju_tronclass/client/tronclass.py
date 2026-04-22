"""TronClass API client：對每個已驗證 endpoint 建一對一的 async method。

只做 HTTP 呼叫 + pydantic 解析，業務邏輯在 services 層。
"""

from __future__ import annotations

from fju_tronclass.client.http import TronClassHttp
from fju_tronclass.errors import SchemaError
from fju_tronclass.logging import get_logger
from fju_tronclass.models.activity import Activity, ActivityListResponse, ActivityReadResult
from fju_tronclass.models.bulletin import Bulletin, BulletinListResponse
from fju_tronclass.models.course import Course, CourseListResponse
from fju_tronclass.models.todo import Todo, TodoListResponse
from fju_tronclass.models.upload import UploadMeta, UploadUrl

logger = get_logger(__name__)


class TronClassClient:
    """輔大 TronClass API 呼叫集中點。"""

    def __init__(self, http: TronClassHttp) -> None:
        self._http = http

    # ------------------------------------------------------------------ #
    # 課程
    # ------------------------------------------------------------------ #

    async def get_my_courses(self, page: int = 1, page_size: int = 20) -> list[Course]:
        """取得我的課程清單。"""
        data = await self._http.get_json(
            "/api/my-courses",
            params={"page": page, "page_size": page_size},
        )
        try:
            return CourseListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("CourseListResponse", data) from e

    # ------------------------------------------------------------------ #
    # 待辦事項
    # ------------------------------------------------------------------ #

    async def get_todos(self) -> list[Todo]:
        """取得所有待辦事項。"""
        data = await self._http.get_json("/api/todos")
        try:
            return TodoListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("TodoListResponse", data) from e

    # ------------------------------------------------------------------ #
    # 公告
    # ------------------------------------------------------------------ #

    async def get_course_bulletins(self, course_id: int) -> list[Bulletin]:
        """取得指定課程的公告列表。"""
        data = await self._http.get_json(
            "/api/course-bulletins",
            params={"course_id": course_id},
        )
        try:
            return BulletinListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("BulletinListResponse", data) from e

    # ------------------------------------------------------------------ #
    # Upload（課程教材）
    # ------------------------------------------------------------------ #

    async def get_upload_url(self, upload_id: int) -> UploadUrl:
        """
        取得 upload 的臨時下載 URL。
        即使 allow_download=false，API 仍會回傳有效 URL（tronclass-downloader 技能已驗證）。
        """
        data = await self._http.get_json(f"/api/uploads/{upload_id}/url")
        try:
            return UploadUrl.model_validate(data)
        except Exception as e:
            raise SchemaError("UploadUrl", data) from e

    async def get_upload_meta(self, upload_id: int) -> UploadMeta:
        """取得 upload 的 metadata（檔名、大小、是否允許下載等）。"""
        data = await self._http.get_json(f"/api/uploads/{upload_id}")
        try:
            return UploadMeta.model_validate(data)
        except Exception as e:
            raise SchemaError("UploadMeta", data) from e

    # ------------------------------------------------------------------ #
    # 活動
    # ------------------------------------------------------------------ #

    async def get_course_activities(self, course_id: int) -> list[Activity]:
        """
        取得課程的所有活動清單（教材與影片）。

        endpoint: GET /api/course/{courseId}/activities
        從 tronclass-downloader 技能逆向：scope.course.activities 由此 endpoint 載入。
        """
        data = await self._http.get_json(f"/api/courses/{course_id}/activities")
        try:
            return ActivityListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("ActivityListResponse", data) from e

    async def get_learning_activity(self, course_id: int, activity_id: int) -> Activity:
        data = await self._http.get_json(f"/api/course/{course_id}/learning-activity/{activity_id}")
        try:
            return Activity.model_validate(data)
        except Exception as e:
            raise SchemaError("Activity", data) from e

    async def post_activity_read(
        self,
        activity_id: int,
        start: int,
        end: int,
        duration: int,
    ) -> ActivityReadResult:
        """
        標記影片觀看進度（tronclass-video-player 技能已驗證）。

        限制：end - start 必須 <= 125 秒（伺服器硬上限）。
        建議使用 services/video.py 中的 mark_video_complete 自動分段。
        """
        if end - start > 125:
            raise ValueError(
                f"每次 post_activity_read 的 end-start 不能超過 125 秒，"
                f"得到 {end - start} 秒。請用 services.video.mark_video_complete 自動分段。"
            )
        data = await self._http.post_json(
            f"/api/course/activities-read/{activity_id}",
            json_body={"start": start, "end": end, "duration": duration},
        )
        try:
            return ActivityReadResult.model_validate(data)
        except Exception as e:
            raise SchemaError("ActivityReadResult", data) from e
