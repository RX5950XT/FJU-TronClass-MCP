"""TronClass API client：對每個已驗證 endpoint 建一對一的 async method。

只做 HTTP 呼叫 + pydantic 解析，業務邏輯在 services 層。
"""

from __future__ import annotations

from typing import Any

from fju_tronclass.client.http import TronClassHttp
from fju_tronclass.errors import SchemaError
from fju_tronclass.logging import get_logger
from fju_tronclass.models.activity import Activity, ActivityListResponse, ActivityReadResult
from fju_tronclass.models.bulletin import Bulletin, BulletinListResponse
from fju_tronclass.models.catalog import (
    CourseModule,
    CourseOutline,
    CourseScore,
    Exam,
    ExamListResponse,
    ForumTopic,
    Profile,
    ScoreItem,
    ScoreItemListResponse,
    TopicListResponse,
)
from fju_tronclass.models.course import Course, CourseListResponse
from fju_tronclass.models.people import (
    GroupSet,
    GroupSetListResponse,
    Homework,
    HomeworkListResponse,
    Person,
)
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

    async def get_my_courses_page(self, page: int = 1, page_size: int = 20) -> CourseListResponse:
        """取得我的課程清單（含 total / 分頁欄位）。"""
        data = await self._http.get_json(
            "/api/my-courses",
            params={"page": page, "page_size": page_size},
        )
        try:
            return CourseListResponse.model_validate(data)
        except Exception as e:
            raise SchemaError("CourseListResponse", data) from e

    async def get_my_courses(self, page: int = 1, page_size: int = 20) -> list[Course]:
        """取得我的課程清單。page=1（預設）會自動翻完所有頁。"""
        if page != 1:
            return (await self.get_my_courses_page(page=page, page_size=page_size)).items
        items: list[Course] = []
        current = 1
        while True:
            resp = await self.get_my_courses_page(page=current, page_size=page_size)
            items.extend(resp.items)
            if len(items) >= resp.total or not resp.items:
                break
            current += 1
        return items

    async def get_course_students(self, course_id: int) -> list[Person]:
        data = await self._http.get_json(f"/api/course/{course_id}/students")
        try:
            items = data.get("students", []) if isinstance(data, dict) else []
            return [Person.model_validate(item) for item in items]
        except Exception as e:
            raise SchemaError("PersonList", data) from e

    async def get_course_enrollments(self, course_id: int) -> list[Person]:
        data = await self._http.get_json(f"/api/course/{course_id}/enrollments")
        try:
            items = data.get("enrollments", []) if isinstance(data, dict) else []
            return [Person.model_validate(item) for item in items]
        except Exception as e:
            raise SchemaError("EnrollmentList", data) from e

    async def get_course_group_sets(self, course_id: int) -> list[GroupSet]:
        data = await self._http.get_json(f"/api/courses/{course_id}/group-sets")
        try:
            return GroupSetListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("GroupSetListResponse", data) from e

    async def get_homework_activities(self, course_id: int) -> list[Homework]:
        data = await self._http.get_json(f"/api/courses/{course_id}/homework-activities")
        try:
            return HomeworkListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("HomeworkListResponse", data) from e

    async def get_profile(self) -> Profile:
        data = await self._http.get_json("/api/profile")
        try:
            return Profile.model_validate(data)
        except Exception as e:
            raise SchemaError("Profile", data) from e

    async def get_course(self, course_id: int) -> dict[str, Any]:
        data = await self._http.get_json(f"/api/courses/{course_id}")
        if not isinstance(data, dict):
            raise SchemaError("CourseDetail", data)
        return data

    async def get_course_modules(self, course_id: int) -> list[CourseModule]:
        data = await self._http.get_json(f"/api/courses/{course_id}/modules")
        try:
            items = data.get("modules", []) if isinstance(data, dict) else []
            return [CourseModule.model_validate(item) for item in items]
        except Exception as e:
            raise SchemaError("CourseModules", data) from e

    async def get_course_outline(self, course_id: int) -> CourseOutline:
        data = await self._http.get_json(f"/api/courses/{course_id}/outline")
        try:
            return CourseOutline.model_validate(data)
        except Exception as e:
            raise SchemaError("CourseOutline", data) from e

    async def get_course_score(self, course_id: int) -> CourseScore:
        data = await self._http.get_json(f"/api/course/{course_id}/score")
        try:
            return CourseScore.model_validate(data)
        except Exception as e:
            raise SchemaError("CourseScore", data) from e

    async def get_score_items(self, course_id: int) -> list[ScoreItem]:
        data = await self._http.get_json(f"/api/courses/{course_id}/score-items")
        try:
            return ScoreItemListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("ScoreItemListResponse", data) from e

    async def get_course_exams(self, course_id: int) -> list[Exam]:
        data = await self._http.get_json(f"/api/courses/{course_id}/exams")
        try:
            return ExamListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("ExamListResponse", data) from e

    async def get_activity(self, activity_id: int) -> dict[str, Any]:
        data = await self._http.get_json(f"/api/activities/{activity_id}")
        if not isinstance(data, dict):
            raise SchemaError("ActivityDetail", data)
        return data

    async def get_homework(self, homework_id: int) -> dict[str, Any]:
        data = await self._http.get_json(f"/api/homework-activities/{homework_id}")
        if not isinstance(data, dict):
            raise SchemaError("HomeworkDetail", data)
        return data

    async def get_forum_topics(self, activity_id: int) -> list[ForumTopic]:
        data = await self._http.get_json(f"/api/activities/{activity_id}/topics")
        try:
            return TopicListResponse.model_validate(data).items
        except Exception as e:
            raise SchemaError("TopicListResponse", data) from e

    async def get_topic(self, topic_id: int) -> dict[str, Any]:
        data = await self._http.get_json(f"/api/topics/{topic_id}")
        if not isinstance(data, dict):
            raise SchemaError("TopicDetail", data)
        return data

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
