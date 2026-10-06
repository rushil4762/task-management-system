import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_created_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "New Lifecycle Task"}, headers=auth_headers)
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    data = act_res.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["action"] == "task_created"
    assert item["activity_type"] == "task_created"
    assert "created this task" in item["message"]
    assert "created this task" in item["description"]
    assert item["metadata"]["title"] == "New Lifecycle Task"
    assert item["user"] is not None
    assert item["user"]["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_task_updated_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Original Title"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Update title
    await client.patch(f"/tasks/{task_id}", json={"title": "Updated Title"}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    # Newest action first
    assert items[0]["action"] == "task_updated"
    assert "Updated Title" in items[0]["description"]
    assert items[0]["metadata"]["new_title"] == "Updated Title"


@pytest.mark.asyncio
async def test_status_changed_completion_and_reopen_activities(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Status Flow Task", "status": "pending"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # 1. Change status to in_progress
    await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers)

    # 2. Mark completed
    await client.patch(f"/tasks/{task_id}/complete", headers=auth_headers)

    # 3. Reopen
    await client.patch(f"/tasks/{task_id}/reopen", headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    actions = [a["action"] for a in items]
    # Expected chronological reverse: task_reopened, task_completed, status_changed, task_created
    assert actions[:3] == ["task_reopened", "task_completed", "status_changed"]

    # Check messages and metadata
    reopened = items[0]
    assert "reopened the task" in reopened["message"]
    assert reopened["metadata"]["old_value"] == "completed"
    assert reopened["metadata"]["new_value"] == "pending"

    completed = items[1]
    assert "completed the task" in completed["message"]
    assert completed["metadata"]["old_value"] == "in_progress"
    assert completed["metadata"]["new_value"] == "completed"

    status_changed = items[2]
    assert "changed status from Pending to In Progress" in status_changed["message"]
    assert status_changed["metadata"]["old_value"] == "pending"
    assert status_changed["metadata"]["new_value"] == "in_progress"


@pytest.mark.asyncio
async def test_priority_changed_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Priority Task", "priority": "low"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    await client.patch(f"/tasks/{task_id}", json={"priority": "urgent"}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    assert items[0]["action"] == "priority_changed"
    assert items[0]["activity_type"] == "priority_changed"
    assert "changed priority from Low to Urgent" in items[0]["message"]
    assert items[0]["metadata"]["old_value"] == "low"
    assert items[0]["metadata"]["new_value"] == "urgent"


@pytest.mark.asyncio
async def test_due_date_changed_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post(
        "/tasks",
        json={"title": "Due Date Task", "due_date": "2026-10-09T10:00:00Z"},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # Change due date from 9 Oct to 10 Oct
    await client.patch(
        f"/tasks/{task_id}",
        json={"due_date": "2026-10-10T10:00:00Z"},
        headers=auth_headers,
    )

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    due_act = items[0]
    assert due_act["action"] == "due_date_changed"
    assert due_act["activity_type"] == "due_date_changed"
    assert "changed due date from 9 Oct to 10 Oct" in due_act["message"]
    assert due_act["metadata"]["old_value"] is not None
    assert due_act["metadata"]["new_value"] is not None


@pytest.mark.asyncio
async def test_task_assigned_activity(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user,
):
    task_res = await client.post("/tasks", json={"title": "Assignment Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Assign
    await client.patch(f"/tasks/{task_id}", json={"assigned_to_id": other_user.id}, headers=auth_headers)

    # Unassign
    await client.patch(f"/tasks/{task_id}", json={"assigned_to_id": None}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    assert items[0]["action"] == "task_assigned"
    assert "unassigned" in items[0]["description"].lower()
    assert items[0]["metadata"]["old_assignee_id"] == other_user.id
    assert items[0]["metadata"]["new_assignee_id"] is None

    assert items[1]["action"] == "task_assigned"
    assert f"assigned task to {other_user.name}" in items[1]["description"]
    assert items[1]["metadata"]["new_assignee_id"] == other_user.id
    assert items[1]["metadata"]["new_assignee_name"] == other_user.name


@pytest.mark.asyncio
async def test_category_changed_activity(client: AsyncClient, auth_headers: dict[str, str]):
    c_res = await client.post("/categories", json={"name": "DevOps"}, headers=auth_headers)
    cat_id = c_res.json()["id"]

    task_res = await client.post("/tasks", json={"title": "Category Activity Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Set category
    await client.patch(f"/tasks/{task_id}", json={"category_id": cat_id}, headers=auth_headers)

    # Remove category
    await client.patch(f"/tasks/{task_id}", json={"category_id": None}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    assert items[0]["action"] == "category_changed"
    assert "removed" in items[0]["description"].lower()
    assert items[0]["metadata"]["old_category_name"] == "DevOps"
    assert items[0]["metadata"]["new_category_id"] is None

    assert items[1]["action"] == "category_changed"
    assert "DevOps" in items[1]["description"]
    assert items[1]["metadata"]["new_category_name"] == "DevOps"


@pytest.mark.asyncio
async def test_tag_added_and_removed_activities(client: AsyncClient, auth_headers: dict[str, str]):
    t1_res = await client.post("/tags", json={"name": "frontend"}, headers=auth_headers)
    tag_id = t1_res.json()["id"]

    task_res = await client.post("/tasks", json={"title": "Tag Activity Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Attach tag
    await client.post(f"/tasks/{task_id}/tags", json={"tag_ids": [tag_id]}, headers=auth_headers)

    # Remove tag
    await client.delete(f"/tasks/{task_id}/tags/{tag_id}", headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    assert items[0]["action"] == "tag_removed"
    assert "frontend" in items[0]["description"]
    assert items[0]["metadata"]["tag_name"] == "frontend"

    assert items[1]["action"] == "tag_added"
    assert "frontend" in items[1]["description"]
    assert items[1]["metadata"]["tag_name"] == "frontend"


@pytest.mark.asyncio
async def test_comment_added_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Comment Activity Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    await client.post(f"/tasks/{task_id}/comments", json={"content": "Hello team"}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    items = act_res.json()["items"]
    assert items[0]["action"] == "comment_added"
    assert "added a comment" in items[0]["message"]
    assert items[0]["metadata"]["comment_id"] is not None


@pytest.mark.asyncio
async def test_activity_contains_correct_actor(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Actor Verification Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    item = act_res.json()["items"][0]

    assert item["user"] is not None
    assert item["user"]["name"] is not None
    assert item["user"]["email"] == "testuser@example.com"
    assert item["user"]["name"] in item["message"]


@pytest.mark.asyncio
async def test_activity_pagination_and_ordering(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Pagination Activity Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Generate multiple updates
    await client.patch(f"/tasks/{task_id}", json={"priority": "high"}, headers=auth_headers)
    await client.patch(f"/tasks/{task_id}", json={"priority": "urgent"}, headers=auth_headers)
    await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers)

    # Total activities: task_created + priority_changed(high) + priority_changed(urgent) + status_changed(in_progress) = 4
    page1 = await client.get(f"/tasks/{task_id}/activities", params={"limit": 2, "offset": 0}, headers=auth_headers)
    assert page1.status_code == 200
    assert len(page1.json()["items"]) == 2
    assert page1.json()["total"] == 4
    assert page1.json()["limit"] == 2
    assert page1.json()["offset"] == 0

    page2 = await client.get(f"/tasks/{task_id}/activities", params={"limit": 2, "offset": 2}, headers=auth_headers)
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 2
    assert page2.json()["total"] == 4
    assert page2.json()["offset"] == 2


@pytest.mark.asyncio
async def test_activity_authorization_and_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    other_user,
):
    # Task assigned to other_user
    task_res = await client.post(
        "/tasks",
        json={"title": "Shared Collab Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # Assignee can view activity history
    assignee_act = await client.get(f"/tasks/{task_id}/activities", headers=other_auth_headers)
    assert assignee_act.status_code == 200
    assert assignee_act.json()["total"] >= 1

    # Unrelated task
    private_res = await client.post("/tasks", json={"title": "Private Owner Task"}, headers=auth_headers)
    private_id = private_res.json()["id"]

    # Other user cannot view private task's activity history
    unauth_act = await client.get(f"/tasks/{private_id}/activities", headers=other_auth_headers)
    assert unauth_act.status_code in [403, 404]


@pytest.mark.asyncio
async def test_unauthenticated_cannot_view_activity(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Auth Gate Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Unauthenticated request -> 401
    res = await client.get(f"/tasks/{task_id}/activities")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_no_duplicate_activities_on_unchanged_values(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post(
        "/tasks",
        json={"title": "Stable Task", "priority": "medium", "status": "pending", "due_date": "2026-10-15T00:00:00Z"},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # PATCH with the exact same values
    await client.patch(
        f"/tasks/{task_id}",
        json={"title": "Stable Task", "priority": "medium", "status": "pending", "due_date": "2026-10-15T00:00:00Z"},
        headers=auth_headers,
    )
    # PATCH with empty dict
    await client.patch(f"/tasks/{task_id}", json={}, headers=auth_headers)

    act_res = await client.get(f"/tasks/{task_id}/activities", headers=auth_headers)
    assert act_res.status_code == 200
    # Only task_created should exist; no duplicate activities recorded
    assert act_res.json()["total"] == 1
    assert act_res.json()["items"][0]["action"] == "task_created"


@pytest.mark.asyncio
async def test_activity_immutability(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Immutable Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # No POST, PUT, PATCH, DELETE endpoints allowed on activities
    post_res = await client.post(f"/tasks/{task_id}/activities", json={"action": "fake"}, headers=auth_headers)
    assert post_res.status_code in [404, 405]

    put_res = await client.put(f"/tasks/{task_id}/activities/1", json={"action": "fake"}, headers=auth_headers)
    assert put_res.status_code in [404, 405]

    patch_res = await client.patch(f"/tasks/{task_id}/activities/1", json={"action": "fake"}, headers=auth_headers)
    assert patch_res.status_code in [404, 405]

    del_res = await client.delete(f"/tasks/{task_id}/activities/1", headers=auth_headers)
    assert del_res.status_code in [404, 405]


@pytest.mark.asyncio
async def test_employee_activity_visibility_rules(
    client: AsyncClient,
    auth_headers: dict[str, str],
    employee_user,
    employee_auth_headers: dict[str, str],
):
    # CEO creates a task not assigned to employee
    task_res = await client.post("/tasks", json={"title": "CEO Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Employee tries to view activities -> 403 Forbidden
    emp_res = await client.get(f"/tasks/{task_id}/activities", headers=employee_auth_headers)
    assert emp_res.status_code == 403

    # CEO assigns task to employee
    await client.patch(f"/tasks/{task_id}/assign", json={"assigned_to_id": employee_user.id}, headers=auth_headers)

    # Now employee CAN view activities -> 200 OK
    emp_res_ok = await client.get(f"/tasks/{task_id}/activities", headers=employee_auth_headers)
    assert emp_res_ok.status_code == 200
    assert emp_res_ok.json()["total"] >= 2

