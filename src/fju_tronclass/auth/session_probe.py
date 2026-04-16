"""Session 探針：用一次輕量 API 呼叫驗證 cookie 是否有效。"""

from __future__ import annotations

from fju_tronclass.errors import SessionExpiredError
from fju_tronclass.logging import get_logger

logger = get_logger(__name__)


async def probe_session(http_client: object) -> int:
    """
    呼叫 /api/my-courses?page_size=1 確認 session 有效。

    Returns:
        課程總數（total 欄位）

    Raises:
        SessionExpiredError: session 已過期或無效
    """
    from fju_tronclass.client.tronclass import TronClassClient

    client = TronClassClient(http_client)  # type: ignore[arg-type]
    try:
        courses = await client.get_my_courses(page=1, page_size=1)
        count = len(courses)
        logger.debug("Session 有效", course_count=count)
        return count
    except SessionExpiredError:
        raise
    except Exception as e:
        logger.warning("Session probe 失敗", error=str(e))
        raise SessionExpiredError() from e
