"""成員、分組、作業服務。"""

from __future__ import annotations

from collections import defaultdict

from fju_tronclass.models.people import CourseGroup, GroupMember, GroupSet, Homework, Person


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
    學生權限下 group-sets 通常只回自己那組的名字，其他組以成員名單呈現。
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
            for gid, members in sorted(clustered.items())
        ]
        return [GroupSet(id=0, name="", group_count=len(groups), groups=groups)]

    result: list[GroupSet] = []
    for gset in sets:
        groups_out: list[CourseGroup] = []
        seen: set[int] = set()
        for gid, members in sorted(clustered.items()):
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
        groups_out.sort(key=lambda g: (g.sort is None, g.sort or 0, g.id))
        result.append(
            GroupSet(
                id=gset.id,
                name=gset.name,
                group_count=max(gset.group_count, len(groups_out)),
                groups=groups_out,
            )
        )
    return result


async def list_homework(client: object, course_id: int) -> list[Homework]:
    items: list[Homework] = await client.get_homework_activities(course_id)  # type: ignore[attr-defined]
    return items
