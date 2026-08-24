"""unit tests for catalog models."""

from __future__ import annotations

from fju_tronclass.models.activity import Activity
from fju_tronclass.models.catalog import CourseOutline, ForumTopic, Profile, html_to_text


def test_html_to_text() -> None:
    assert "電子學" in html_to_text("<p>電子學<br>二</p>")


def test_profile_normalizes_department() -> None:
    profile = Profile.model_validate(
        {
            "id": 1,
            "name": "陳庠端",
            "user_no": "413610290",
            "email": "a@b.c",
            "department": {"name": "電子物理組"},
            "grade": {"name": "二年級"},
            "roles": [{"id": 2, "name": "Student"}],
            "total_course": 40,
        }
    )
    assert profile.department == "電子物理組"
    assert profile.grade == "二年級"
    assert profile.roles == ["Student"]


def test_outline_from_comment_chinese() -> None:
    outline = CourseOutline.model_validate(
        {"id": 1, "comment_chinese": {"description": "<p>大綱</p>"}}
    )
    assert outline.description == "<p>大綱</p>"


def test_forum_topic_author() -> None:
    topic = ForumTopic.model_validate(
        {"id": 1, "title": "t", "content": "<p>x</p>", "created_by": {"name": "藍婌瑞"}, "like_count": 1}
    )
    assert topic.author == "藍婌瑞"


def test_activity_type_label_and_link() -> None:
    act = Activity.model_validate(
        {"id": 1, "title": "電路", "type": "web_link", "data": {"link": "https://example.com"}}
    )
    assert act.type_label == "連結"
    assert act.extra_text == "https://example.com"
