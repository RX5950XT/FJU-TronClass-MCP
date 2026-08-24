"""成員、分組、作業服務。"""

from __future__ import annotations

from collections import defaultdict

from fju_tronclass.models.people import CourseGroup, GroupMember, GroupSet, Homework, Person


_CN = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
    11: "十一",
    12: "十二",
    13: "十三",
    14: "十四",
    15: "十五",
}


def _ordinal_name(index: int) -> str:
    return f"第{_CN.get(index, str(index))}組"


def _fill_group_names(groups: list[CourseGroup]) -> list[CourseGroup]:
    """用官方 group_id 排序補「第 N 組」。不掃 ID、不打 submission。"""
    ordered = sorted(groups, key=lambda g: g.id)
    filled: list[CourseGroup] = []
    for index, group in enumerate(ordered, start=1):
        filled.append(
            CourseGroup(
                id=group.id,
                name=group.name or _ordinal_name(index),
                sort=group.sort or index,
                members=group.members,
            )
        )
    return filled


async def list_people(client: object, course_id: int, role: str | None = None) -> list[Person]:
    """課程成員：學生走 students API，教師/助教從 enrollments 補。"""
    students = await client.get_course_students(course_id)  # type: ignore[attr-defined]
    enrollments = await client.get_course_enrollments(course_id)  # type: ignore[attr-defined]
    by_id = {p.id: p for p in students}
    for person in enrollments:
        if person.id not in by_id or person.roles and not by_id[person.id].roles:
            by_id[person.id] = person
    people = list(by_id.values())
    if role:
        people = [p for p in people if role in p.roles]
    people.sort(key=lambda p: (p.role_label, p.user_no or "", p.name))
    return people


async def list_groups(client: object, course_id: int) -> list[GroupSet]:
    """
    用官方 students.group_ids 聚合成組，再用 group-sets 補組名。
    沒有官方組名的，依 group_id 排序標成第 N 組。
    """
    students = await client.get_course_students(course_id)  # type: ignore[attr-defined]
    sets = await client.get_course_group_sets(course_id)  # type: ignore[attr-defined]
    named: dict[int, CourseGroup] = {}
    for gset in sets:
        for group in gset.groups:
            named[group.id] = group

    clustered: dict[int, list[Person]] = defaultdict(list)
    for person in students:
        for gid in person.group_ids:
            clustered[gid].append(person)

    if not sets and not clustered:
        return []

    if not sets:
        groups = [
            CourseGroup(
                id=gid,
                name="",
                members=[GroupMember(id=p.id, name=p.name, user_no=p.user_no) for p in members],
            )
            for gid, members in clustered.items()
        ]
        return [GroupSet(id=0, name="", group_count=len(groups), groups=_fill_group_names(groups))]

    result: list[GroupSet] = []
    for gset in sets:
        groups_out: list[CourseGroup] = []
        seen: set[int] = set()
        for gid, members in clustered.items():
            seen.add(gid)
            known = named.get(gid)
            groups_out.append(
                CourseGroup(
                    id=gid,
                    name=known.name if known else "",
                    sort=known.sort if known else None,
                    members=[GroupMember(id=p.id, name=p.name, user_no=p.user_no) for p in members],
                )
            )
        for group in gset.groups:
            if group.id not in seen:
                groups_out.append(group)
        result.append(
            GroupSet(
                id=gset.id,
                name=gset.name,
                group_count=max(gset.group_count, len(groups_out)),
                groups=_fill_group_names(groups_out),
            )
        )
    return result


async def list_homework(client: object, course_id: int) -> list[Homework]:
    items: list[Homework] = await client.get_homework_activities(course_id)  # type: ignore[attr-defined]
    return items
