"""unit tests for people / groups / homework models and services."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from fju_tronclass.models.people import GroupSet, Homework, Person


def test_person_from_student_payload() -> None:
    person = Person.model_validate(
        {
            "id": 492902,
            "name": "陳庠端",
            "user_no": "413610290",
            "roles": ["student"],
            "group_ids": [445725],
            "department": {"name": "電子物理組"},
            "grade": {"name": "二年級"},
        }
    )
    assert person.role_label == "學生"
    assert person.department == "電子物理組"
    assert person.grade == "二年級"


def test_person_from_enrollment_payload() -> None:
    person = Person.model_validate(
        {
            "id": 1,
            "roles": ["instructor"],
            "user": {"id": 20419, "name": "張敏娟", "user_no": "068190"},
        }
    )
    assert person.name == "張敏娟"
    assert person.user_no == "068190"
    assert person.id == 20419
    assert person.role_label == "教師"


def test_group_set_ignores_numeric_members() -> None:
    gset = GroupSet.model_validate(
        {
            "id": 219432,
            "name": "期中報告",
            "group_count": 15,
            "groups": [{"id": 445725, "name": "第四組", "sort": 4, "members": [492902, 492914]}],
        }
    )
    assert gset.groups[0].name == "第四組"
    assert gset.groups[0].members == []


def test_homework_parses_deadline() -> None:
    hw = Homework.model_validate(
        {
            "id": 1,
            "title": "期中",
            "deadline": "2026-06-23T15:59:00Z",
            "submitted": True,
            "score": "A",
        }
    )
    assert hw.due is not None
    assert hw.submitted is True
    assert hw.score == "A"


@pytest.mark.asyncio
async def test_list_groups_clusters_students() -> None:
    from fju_tronclass.services.people import list_groups

    client = AsyncMock()
    client.get_course_students.return_value = [
        Person(id=1, name="甲", user_no="1", group_ids=[10]),
        Person(id=2, name="乙", user_no="2", group_ids=[10]),
        Person(id=3, name="丙", user_no="3", group_ids=[20]),
    ]
    client.get_course_group_sets.return_value = [
        GroupSet.model_validate(
            {
                "id": 99,
                "name": "期中",
                "group_count": 2,
                "groups": [{"id": 10, "name": "第一組", "sort": 1, "members": [1, 2]}],
            }
        )
    ]
    sets = await list_groups(client, 374430)
    assert sets[0].name == "期中"
    assert [g.id for g in sets[0].groups] == [10, 20]
    assert sets[0].groups[0].name == "第一組"
    assert [m.name for m in sets[0].groups[0].members] == ["甲", "乙"]
    assert sets[0].groups[1].name == "第二組"
    assert [m.name for m in sets[0].groups[1].members] == ["丙"]
