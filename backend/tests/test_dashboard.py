from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_unauthenticated_access(client: AsyncClient):
    """Verify all dashboard endpoints enforce authentication."""
    r1 = await client.get("/dashboard/summary")
    assert r1.status_code == 401

    r2 = await client.get("/dashboard/completion-trend")
    assert r2.status_code == 401

    r3 = await client.get("/dashboard/recent-activity")
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_summary_zero_tasks(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify safe zero handling and default responses when user has no tasks."""
    response = await client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Total task status breakdown
    assert data["total_tasks"]["total"] == 0
    assert data["total_tasks"]["pending"] == 0
    assert data["total_tasks"]["in_progress"] == 0
    assert data["total_tasks"]["completed"] == 0
    assert data["total_tasks"]["cancelled"] == 0

    # Aliases
    assert data["tasks"]["total"] == 0

    # Priorities
    assert data["priority_summary"]["low"] == 0
    assert data["priority_summary"]["medium"] == 0
    assert data["priority_summary"]["high"] == 0
    assert data["priority_summary"]["urgent"] == 0

    # Due dates
    assert data["due_date_summary"]["overdue"] == 0
    assert data["due_date_summary"]["due_today"] == 0
    assert data["due_date_summary"]["due_this_week"] == 0
    assert data["due_date_summary"]["upcoming"] == 0

    # Completion metrics (zero division safety)
    assert data["completion_metrics"]["total_completed"] == 0
    assert data["completion_metrics"]["completion_percentage"] == 0.0

    # Categories and trend
    assert data["category_summary"] == []
    assert data["completion_trend"] == []


@pytest.mark.asyncio
async def test_dashboard_summary_status_and_priorities(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify task status counts, priority breakdown, and completion percentage."""
    # 2 pending, 1 in_progress, 2 completed, 1 cancelled = 6 total
    # 1 low, 2 medium, 2 high, 1 urgent = 6 total
    tasks_to_create = [
        {"title": "Task 1", "status": "pending", "priority": "low"},
        {"title": "Task 2", "status": "pending", "priority": "medium"},
        {"title": "Task 3", "status": "in_progress", "priority": "medium"},
        {"title": "Task 4", "status": "completed", "priority": "high"},
        {"title": "Task 5", "status": "completed", "priority": "high"},
        {"title": "Task 6", "status": "cancelled", "priority": "urgent"},
    ]

    for t in tasks_to_create:
        res = await client.post("/tasks", json=t, headers=auth_headers)
        assert res.status_code == 201

    response = await client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Status counts
    assert data["total_tasks"]["total"] == 6
    assert data["total_tasks"]["pending"] == 2
    assert data["total_tasks"]["in_progress"] == 1
    assert data["total_tasks"]["completed"] == 2
    assert data["total_tasks"]["cancelled"] == 1

    # Priority counts
    assert data["priority_summary"]["low"] == 1
    assert data["priority_summary"]["medium"] == 2
    assert data["priority_summary"]["high"] == 2
    assert data["priority_summary"]["urgent"] == 1

    # Completion percentage: 2 / 6 * 100 = 33.33%
    assert data["completion_metrics"]["total_completed"] == 2
    assert data["completion_metrics"]["completion_percentage"] == 33.33


@pytest.mark.asyncio
async def test_dashboard_summary_due_date_boundaries(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """
    Verify due date metrics:
    - overdue: past due and not completed or cancelled
    - due_today: due today and not completed or cancelled
    - due_this_week: due within 7 days from today and not completed or cancelled
    - upcoming: due strictly after today and not completed or cancelled
    - completed/cancelled tasks must never be counted as overdue
    """
    now = datetime.now(timezone.utc)
    past_due = (now - timedelta(days=2)).isoformat()
    future_today = (now + timedelta(minutes=30)).isoformat()
    this_week = (now + timedelta(days=3)).isoformat()
    next_month = (now + timedelta(days=20)).isoformat()

    # 1. Overdue active task -> should be overdue
    await client.post(
        "/tasks",
        json={"title": "Overdue Pending", "due_date": past_due, "status": "pending"},
        headers=auth_headers,
    )
    # 2. Overdue completed task -> must NOT be overdue
    await client.post(
        "/tasks",
        json={"title": "Overdue Completed", "due_date": past_due, "status": "completed"},
        headers=auth_headers,
    )
    # 3. Overdue cancelled task -> must NOT be overdue
    await client.post(
        "/tasks",
        json={"title": "Overdue Cancelled", "due_date": past_due, "status": "cancelled"},
        headers=auth_headers,
    )
    # 4. Due today active task -> due_today and due_this_week
    await client.post(
        "/tasks",
        json={"title": "Due Today", "due_date": future_today, "status": "pending"},
        headers=auth_headers,
    )
    # 5. Due in 3 days active task -> due_this_week and upcoming
    await client.post(
        "/tasks",
        json={"title": "Due This Week", "due_date": this_week, "status": "in_progress"},
        headers=auth_headers,
    )
    # 6. Due in 20 days active task -> upcoming only
    await client.post(
        "/tasks",
        json={"title": "Upcoming Far", "due_date": next_month, "status": "pending"},
        headers=auth_headers,
    )

    response = await client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    due_dates = data["due_date_summary"]

    assert due_dates["overdue"] == 1
    assert due_dates["due_today"] == 1
    assert due_dates["due_this_week"] == 2  # due today + due in 3 days
    assert due_dates["upcoming"] == 2  # due in 3 days + due in 20 days


@pytest.mark.asyncio
async def test_dashboard_category_summary_and_uncategorized(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify category summary returns task counts grouped by category and includes uncategorized tasks."""
    # Create categories
    cat1_res = await client.post(
        "/categories",
        json={"name": "Work", "description": "Work items"},
        headers=auth_headers,
    )
    cat1_id = cat1_res.json()["id"]

    cat2_res = await client.post(
        "/categories",
        json={"name": "Personal", "description": "Personal items"},
        headers=auth_headers,
    )
    cat2_id = cat2_res.json()["id"]

    # Create tasks in cat1
    await client.post(
        "/tasks",
        json={"title": "Work 1", "category_id": cat1_id},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "Work 2", "category_id": cat1_id},
        headers=auth_headers,
    )

    # Create task in cat2
    await client.post(
        "/tasks",
        json={"title": "Personal 1", "category_id": cat2_id},
        headers=auth_headers,
    )

    # Create 3 uncategorized tasks
    for i in range(3):
        await client.post(
            "/tasks",
            json={"title": f"Uncategorized {i+1}", "category_id": None},
            headers=auth_headers,
        )

    response = await client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    cat_summary = response.json()["category_summary"]

    # Verify counts
    summary_map = {item["category_name"]: item["task_count"] for item in cat_summary}
    assert summary_map["Work"] == 2
    assert summary_map["Personal"] == 1
    assert summary_map["Uncategorized"] == 3

    # Check uncategorized category_id is None
    uncategorized_item = next(item for item in cat_summary if item["category_name"] == "Uncategorized")
    assert uncategorized_item["category_id"] is None


@pytest.mark.asyncio
async def test_dashboard_completion_trend_endpoint(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify /dashboard/completion-trend aggregates completions by date."""
    # Complete 2 tasks
    await client.post(
        "/tasks",
        json={"title": "Completed 1", "status": "completed"},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "Completed 2", "status": "completed"},
        headers=auth_headers,
    )
    # 1 non-completed task
    await client.post(
        "/tasks",
        json={"title": "Pending 1", "status": "pending"},
        headers=auth_headers,
    )

    res = await client.get("/dashboard/completion-trend", headers=auth_headers)
    assert res.status_code == 200
    points = res.json()
    assert len(points) >= 1
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_point = next((p for p in points if p["date"] == today_str), None)
    assert today_point is not None
    assert today_point["completed"] == 2

    # Test date range validation
    invalid_res = await client.get(
        "/dashboard/completion-trend",
        params={"start_date": "2026-10-10", "end_date": "2026-09-01"},
        headers=auth_headers,
    )
    assert invalid_res.status_code == 400


@pytest.mark.asyncio
async def test_dashboard_recent_activity_endpoint(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify /dashboard/recent-activity returns newest-first activities with pagination."""
    task_res = await client.post(
        "/tasks",
        json={"title": "Activity Task", "priority": "low"},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # Update task to generate activity
    await client.put(
        f"/tasks/{task_id}",
        json={"priority": "urgent"},
        headers=auth_headers,
    )

    # Post comment to generate activity
    await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Dashboard activity test comment"},
        headers=auth_headers,
    )

    res = await client.get("/dashboard/recent-activity?limit=10&offset=0", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    assert len(items) >= 3
    assert data["total"] >= 3

    # Newest-first check
    dates = [datetime.fromisoformat(item["created_at"]) for item in items]
    for i in range(len(dates) - 1):
        assert dates[i] >= dates[i + 1]


@pytest.mark.asyncio
async def test_dashboard_user_isolation_security(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    """
    Verify complete multi-user data isolation:
    User A cannot see User B's statistics, categories, completion trends, or activities.
    """
    # User A creates 2 tasks and 1 category
    cat_a = await client.post(
        "/categories",
        json={"name": "UserA Category"},
        headers=auth_headers,
    )
    cat_a_id = cat_a.json()["id"]

    await client.post(
        "/tasks",
        json={"title": "UserA Task 1", "status": "completed", "category_id": cat_a_id},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "UserA Task 2", "status": "pending", "category_id": cat_a_id},
        headers=auth_headers,
    )

    # User B creates 3 tasks (2 completed) and 1 category
    cat_b = await client.post(
        "/categories",
        json={"name": "UserB Category"},
        headers=other_auth_headers,
    )
    cat_b_id = cat_b.json()["id"]

    await client.post(
        "/tasks",
        json={"title": "UserB Task 1", "status": "completed", "category_id": cat_b_id},
        headers=other_auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "UserB Task 2", "status": "completed", "category_id": cat_b_id},
        headers=other_auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "UserB Task 3", "status": "in_progress", "category_id": cat_b_id},
        headers=other_auth_headers,
    )

    # Verify User A dashboard
    res_a = await client.get("/dashboard/summary", headers=auth_headers)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total_tasks"]["total"] == 2
    assert data_a["total_tasks"]["completed"] == 1
    assert data_a["total_tasks"]["pending"] == 1
    assert data_a["completion_metrics"]["total_completed"] == 1
    # Category summary for User A
    cat_names_a = [c["category_name"] for c in data_a["category_summary"]]
    assert "UserA Category" in cat_names_a
    assert "UserB Category" not in cat_names_a

    # Verify User B dashboard
    res_b = await client.get("/dashboard/summary", headers=other_auth_headers)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total_tasks"]["total"] == 3
    assert data_b["total_tasks"]["completed"] == 2
    assert data_b["total_tasks"]["in_progress"] == 1
    assert data_b["completion_metrics"]["total_completed"] == 2
    # Category summary for User B
    cat_names_b = [c["category_name"] for c in data_b["category_summary"]]
    assert "UserB Category" in cat_names_b
    assert "UserA Category" not in cat_names_b

    # Verify Completion Trend isolation
    trend_a = await client.get("/dashboard/completion-trend", headers=auth_headers)
    assert trend_a.status_code == 200
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_a = next((p for p in trend_a.json() if p["date"] == today_str), None)
    assert today_a is not None
    assert today_a["completed"] == 1  # User A only has 1 completed task

    trend_b = await client.get("/dashboard/completion-trend", headers=other_auth_headers)
    assert trend_b.status_code == 200
    today_b = next((p for p in trend_b.json() if p["date"] == today_str), None)
    assert today_b is not None
    assert today_b["completed"] == 2  # User B has 2 completed tasks

    # Verify Activity isolation
    act_a = await client.get("/dashboard/recent-activity", headers=auth_headers)
    assert act_a.status_code == 200
    for item in act_a.json()["items"]:
        assert "UserB" not in item["description"]

    act_b = await client.get("/dashboard/recent-activity", headers=other_auth_headers)
    assert act_b.status_code == 200
    for item in act_b.json()["items"]:
        assert "UserA" not in item["description"]
