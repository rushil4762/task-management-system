from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services import reminder_service


@pytest.mark.asyncio
async def test_notification_unauthenticated_access(client: AsyncClient):
    """Verify all notification endpoints require valid JWT authentication."""
    r1 = await client.get("/notifications")
    assert r1.status_code == 401

    r2 = await client.get("/notifications/unread-count")
    assert r2.status_code == 401

    r3 = await client.patch("/notifications/1/read")
    assert r3.status_code == 401

    r4 = await client.patch("/notifications/read-all")
    assert r4.status_code == 401


@pytest.mark.asyncio
async def test_task_assignment_notification_and_self_assignment(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """
    Verify:
    - Task assignment to another user creates a task_assigned notification for the assignee.
    - Self-assignment does not create an assignment notification.
    """
    # 1. User A assigns task to User B
    create_res = await client.post(
        "/tasks",
        json={"title": "Team Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    assert create_res.status_code == 201

    # User B should have 1 unread notification
    notifs_b = await client.get("/notifications", headers=other_auth_headers)
    assert notifs_b.status_code == 200
    data_b = notifs_b.json()
    assert data_b["total"] == 1
    assert data_b["unread_count"] == 1
    assert data_b["items"][0]["type"] == NotificationType.TASK_ASSIGNED.value
    assert "Team Task" in data_b["items"][0]["title"]

    # User A (creator) should NOT have any notifications
    notifs_a = await client.get("/notifications", headers=auth_headers)
    assert notifs_a.status_code == 200
    assert notifs_a.json()["total"] == 0

    # 2. User A creates a task without assignment (or self-assigned)
    self_task_res = await client.post(
        "/tasks",
        json={"title": "Solo Task"},
        headers=auth_headers,
    )
    assert self_task_res.status_code == 201

    # User A should still have 0 notifications
    notifs_a2 = await client.get("/notifications", headers=auth_headers)
    assert notifs_a2.json()["total"] == 0


@pytest.mark.asyncio
async def test_task_completion_notification_and_duplicate_prevention(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """
    Verify:
    - Marking task completed creates a task_completed notification.
    - Marking an already completed task does not produce duplicate notifications.
    """
    create_res = await client.post(
        "/tasks",
        json={"title": "Finish Report", "status": "pending"},
        headers=auth_headers,
    )
    task_id = create_res.json()["id"]

    # Mark completed
    complete_res = await client.patch(f"/tasks/{task_id}/complete", headers=auth_headers)
    assert complete_res.status_code == 200

    notifs = await client.get("/notifications", headers=auth_headers)
    assert notifs.status_code == 200
    data = notifs.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == NotificationType.TASK_COMPLETED.value
    assert "Finish Report" in data["items"][0]["title"]

    # Complete again (idempotent / already completed)
    complete_res2 = await client.patch(f"/tasks/{task_id}/complete", headers=auth_headers)
    assert complete_res2.status_code == 200

    notifs2 = await client.get("/notifications", headers=auth_headers)
    # Total should still be 1 (no duplicate notification)
    assert notifs2.json()["total"] == 1


@pytest.mark.asyncio
async def test_comment_notification_author_exclusion(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """
    Verify:
    - When User B comments on User A's task, User A receives a comment_added notification.
    - User B (comment author) does not receive their own notification.
    """
    # User A creates a task assigned to User B
    create_res = await client.post(
        "/tasks",
        json={"title": "Discussion Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    task_id = create_res.json()["id"]

    # User B posts a comment
    comment_res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Here is my progress update"},
        headers=other_auth_headers,
    )
    assert comment_res.status_code == 201

    # User A should receive a comment_added notification
    notifs_a = await client.get("/notifications", headers=auth_headers)
    assert notifs_a.status_code == 200
    data_a = notifs_a.json()
    assert data_a["total"] == 1
    assert data_a["items"][0]["type"] == NotificationType.COMMENT_ADDED.value
    assert "Discussion Task" in data_a["items"][0]["title"]

    # User B should only have the initial task_assigned notification, NOT a comment notification
    notifs_b = await client.get("/notifications", headers=other_auth_headers)
    assert notifs_b.status_code == 200
    types_b = [item["type"] for item in notifs_b.json()["items"]]
    assert NotificationType.COMMENT_ADDED.value not in types_b


@pytest.mark.asyncio
async def test_notifications_listing_pagination_and_filtering(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """Verify pagination and filtering by is_read and notification type."""
    # Create 3 tasks with User B assigned so User B gets 3 notifications
    for i in range(3):
        await client.post(
            "/tasks",
            json={"title": f"Task {i+1}", "assigned_to_id": other_user.id},
            headers=auth_headers,
        )

    # User B checks notifications
    all_notifs = await client.get("/notifications", headers=other_auth_headers)
    assert all_notifs.status_code == 200
    assert all_notifs.json()["total"] == 3

    # Mark 1 as read
    first_id = all_notifs.json()["items"][0]["id"]
    await client.patch(f"/notifications/{first_id}/read", headers=other_auth_headers)

    # Filter is_read=true
    read_res = await client.get("/notifications", params={"is_read": True}, headers=other_auth_headers)
    assert read_res.status_code == 200
    assert read_res.json()["total"] == 1
    assert read_res.json()["items"][0]["id"] == first_id

    # Filter is_read=false
    unread_res = await client.get("/notifications", params={"is_read": False}, headers=other_auth_headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["total"] == 2

    # Filter by type=task_assigned
    type_res = await client.get("/notifications", params={"type": "task_assigned"}, headers=other_auth_headers)
    assert type_res.status_code == 200
    assert type_res.json()["total"] == 3

    # Filter by non-existent type
    empty_type = await client.get("/notifications", params={"type": "task_overdue"}, headers=other_auth_headers)
    assert empty_type.status_code == 200
    assert empty_type.json()["total"] == 0

    # Test pagination
    page1 = await client.get("/notifications", params={"limit": 2, "offset": 0}, headers=other_auth_headers)
    assert page1.status_code == 200
    assert len(page1.json()["items"]) == 2

    page2 = await client.get("/notifications", params={"limit": 2, "offset": 2}, headers=other_auth_headers)
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_unread_count_and_mark_as_read(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """Verify unread-count and mark notification as read."""
    # Assign 2 tasks to User B
    await client.post("/tasks", json={"title": "T1", "assigned_to_id": other_user.id}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T2", "assigned_to_id": other_user.id}, headers=auth_headers)

    # Unread count should be 2
    count_res = await client.get("/notifications/unread-count", headers=other_auth_headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] == 2

    # Mark 1 as read
    notifs = await client.get("/notifications", headers=other_auth_headers)
    notif_id = notifs.json()["items"][0]["id"]

    read_res = await client.patch(f"/notifications/{notif_id}/read", headers=other_auth_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Unread count should now be 1
    count_res2 = await client.get("/notifications/unread-count", headers=other_auth_headers)
    assert count_res2.json()["unread_count"] == 1


@pytest.mark.asyncio
async def test_read_all_notifications_user_scoped(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """Verify read-all marks all unread notifications for current user and isolates other users."""
    # Assign 2 tasks to User B
    await client.post("/tasks", json={"title": "T1", "assigned_to_id": other_user.id}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T2", "assigned_to_id": other_user.id}, headers=auth_headers)

    # User B assigns 1 task to User A
    await client.post("/tasks", json={"title": "T3", "assigned_to_id": test_user.id}, headers=other_auth_headers)

    # User B calls read-all
    read_all_res = await client.patch("/notifications/read-all", headers=other_auth_headers)
    assert read_all_res.status_code == 200
    assert read_all_res.json()["updated_count"] == 2

    # User B unread count should be 0
    count_b = await client.get("/notifications/unread-count", headers=other_auth_headers)
    assert count_b.json()["unread_count"] == 0

    # User A unread count should STILL be 1 (unaffected)
    count_a = await client.get("/notifications/unread-count", headers=auth_headers)
    assert count_a.json()["unread_count"] == 1


@pytest.mark.asyncio
async def test_cannot_modify_another_user_notification(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user: User,
    other_auth_headers: dict[str, str],
):
    """Verify user cannot mark another user's notification as read."""
    # Assign task to User B
    await client.post("/tasks", json={"title": "Private Task", "assigned_to_id": other_user.id}, headers=auth_headers)

    # Get User B's notification id
    notifs_b = await client.get("/notifications", headers=other_auth_headers)
    notif_id = notifs_b.json()["items"][0]["id"]

    # User A attempts to mark User B's notification as read
    forbidden_res = await client.patch(f"/notifications/{notif_id}/read", headers=auth_headers)
    assert forbidden_res.status_code in [403, 404]

    # Non-existent notification id
    not_found_res = await client.patch("/notifications/999999/read", headers=auth_headers)
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_reminder_service_detection_and_duplicate_prevention(
    db_session: AsyncSession,
    test_user: User,
):
    """
    Verify reminder service:
    - Identifies tasks due soon (< 24h) and overdue (< now)
    - Excludes completed and cancelled tasks from overdue
    - Prevents duplicates on repeated execution
    """
    now = datetime.now(timezone.utc)
    due_soon_date = now + timedelta(hours=10)
    far_future_date = now + timedelta(hours=72)
    past_date = now - timedelta(hours=5)

    # 1. Active task due soon -> should trigger task_due_soon
    t1 = Task(
        title="Due Soon Task",
        due_date=due_soon_date,
        status=TaskStatus.PENDING,
        user_id=test_user.id,
    )
    # 2. Active task far future -> should NOT trigger
    t2 = Task(
        title="Future Task",
        due_date=far_future_date,
        status=TaskStatus.PENDING,
        user_id=test_user.id,
    )
    # 3. Active task overdue -> should trigger task_overdue
    t3 = Task(
        title="Overdue Task",
        due_date=past_date,
        status=TaskStatus.IN_PROGRESS,
        user_id=test_user.id,
    )
    # 4. Completed task with past due date -> should NOT trigger overdue
    t4 = Task(
        title="Completed Past Task",
        due_date=past_date,
        status=TaskStatus.COMPLETED,
        user_id=test_user.id,
    )
    # 5. Cancelled task with past due date -> should NOT trigger overdue
    t5 = Task(
        title="Cancelled Past Task",
        due_date=past_date,
        status=TaskStatus.CANCELLED,
        user_id=test_user.id,
    )
    db_session.add_all([t1, t2, t3, t4, t5])
    await db_session.commit()

    # First run of reminder service
    result1 = await reminder_service.run_all_reminders(db_session)
    assert result1["due_soon_reminders"] == 1
    assert result1["overdue_reminders"] == 1

    # Second run of reminder service (duplicate prevention check)
    result2 = await reminder_service.run_all_reminders(db_session)
    assert result2["due_soon_reminders"] == 0
    assert result2["overdue_reminders"] == 0
