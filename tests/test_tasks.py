from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_unauthenticated_tasks_access(client: AsyncClient):
    # GET /tasks without token
    res = await client.get("/tasks")
    assert res.status_code == 401

    # POST /tasks without token
    res = await client.post("/tasks", json={"title": "Unauthorized Task"})
    assert res.status_code == 401

    # GET /tasks/1 without token
    res = await client.get("/tasks/1")
    assert res.status_code == 401

    # PUT /tasks/1 without token
    res = await client.put("/tasks/1", json={"title": "Unauthorized Update"})
    assert res.status_code == 401

    # DELETE /tasks/1 without token
    res = await client.delete("/tasks/1")
    assert res.status_code == 401

    # Complete / Reopen without token
    res = await client.patch("/tasks/1/complete")
    assert res.status_code == 401
    res = await client.patch("/tasks/1/reopen")
    assert res.status_code == 401

    # Bulk delete without token
    res = await client.post("/tasks/bulk-delete", json={"task_ids": [1, 2]})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict[str, str], test_user):
    due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "Test Task",
        "description": "Testing AsyncClient with Auth and Due Date",
        "status": "pending",
        "priority": "urgent",
        "due_date": due,
    }
    response = await client.post("/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Test Task"
    assert data["description"] == "Testing AsyncClient with Auth and Due Date"
    assert data["status"] == "pending"
    assert data["priority"] == "urgent"
    assert data["due_date"] is not None
    assert data["completed_at"] is None
    assert data["user_id"] == test_user.id
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_task_validation_errors(client: AsyncClient, auth_headers: dict[str, str]):
    # Empty title
    response = await client.post("/tasks", json={"title": ""}, headers=auth_headers)
    assert response.status_code == 422

    # Whitespace-only title
    response = await client.post("/tasks", json={"title": "   "}, headers=auth_headers)
    assert response.status_code == 422

    # Invalid status
    response = await client.post(
        "/tasks",
        json={"title": "Valid Title", "status": "unknown_status"},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid priority
    response = await client.post(
        "/tasks",
        json={"title": "Valid Title", "priority": "super_critical"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post(
        "/tasks",
        json={"title": "Fetchable Task", "priority": "low"},
        headers=auth_headers,
    )
    task_id = create_res.json()["id"]

    # Successful retrieval
    get_res = await client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Fetchable Task"

    # Non-existent task ID
    not_found = await client.get("/tasks/99999", headers=auth_headers)
    assert not_found.status_code == 404
    assert not_found.json()["detail"] == "Task not found"

    # Invalid task ID (path validation ge=1)
    invalid_id = await client.get("/tasks/0", headers=auth_headers)
    assert invalid_id.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient, auth_headers: dict[str, str]):
    # Create 5 tasks
    for i in range(5):
        await client.post("/tasks", json={"title": f"Task {i}"}, headers=auth_headers)

    # Page 1 (limit 2, offset 0)
    page1 = await client.get("/tasks", params={"limit": 2, "offset": 0}, headers=auth_headers)
    assert page1.status_code == 200
    data1 = page1.json()
    assert len(data1["items"]) == 2
    assert data1["total"] == 5
    assert data1["limit"] == 2
    assert data1["offset"] == 0

    # Page 2 (limit 2, offset 2)
    page2 = await client.get("/tasks", params={"limit": 2, "offset": 2}, headers=auth_headers)
    assert page2.status_code == 200
    data2 = page2.json()
    assert len(data2["items"]) == 2
    assert data2["total"] == 5
    assert data2["offset"] == 2


@pytest.mark.asyncio
async def test_list_tasks_status_and_priority_filtering(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/tasks", json={"title": "Task A", "status": "pending", "priority": "low"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Task B", "status": "in_progress", "priority": "urgent"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Task C", "status": "cancelled", "priority": "high"}, headers=auth_headers)

    # Filter by status cancelled
    res_status = await client.get("/tasks", params={"status": "cancelled"}, headers=auth_headers)
    assert res_status.status_code == 200
    assert res_status.json()["total"] == 1
    assert res_status.json()["items"][0]["title"] == "Task C"

    # Filter by priority urgent
    res_priority = await client.get("/tasks", params={"priority": "urgent"}, headers=auth_headers)
    assert res_priority.status_code == 200
    assert res_priority.json()["total"] == 1
    assert res_priority.json()["items"][0]["title"] == "Task B"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tasks", json={"title": "Original Title"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    # PUT partial/full update
    update_res = await client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated Title", "priority": "urgent"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated Title"
    assert updated["priority"] == "urgent"

    # PATCH endpoint
    patch_res = await client.patch(
        f"/tasks/{task_id}",
        json={"description": "Updated Description"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["description"] == "Updated Description"

    # Updating non-existent task
    not_found = await client.put("/tasks/9999", json={"title": "New"}, headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tasks", json={"title": "Task to Delete"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    # Delete existing task
    delete_res = await client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert delete_res.status_code == 204

    # Verify task is deleted
    get_res = await client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 404

    # Deleting non-existent task
    del_not_found = await client.delete("/tasks/9999", headers=auth_headers)
    assert del_not_found.status_code == 404


@pytest.mark.asyncio
async def test_mark_task_completed_and_reopen(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create a pending task
    res = await client.post(
        "/tasks",
        json={"title": "Task to complete", "status": "pending"},
        headers=auth_headers,
    )
    task_id = res.json()["id"]
    assert res.json()["completed_at"] is None

    # 2. Mark completed via dedicated endpoint
    complete_res = await client.patch(f"/tasks/{task_id}/complete", headers=auth_headers)
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["status"] == "completed"
    assert comp_data["completed_at"] is not None

    # 3. Reopen task via dedicated endpoint
    reopen_res = await client.patch(f"/tasks/{task_id}/reopen", headers=auth_headers)
    assert reopen_res.status_code == 200
    reopen_data = reopen_res.json()
    assert reopen_data["status"] == "pending"
    assert reopen_data["completed_at"] is None


@pytest.mark.asyncio
async def test_status_change_auto_completed_at(client: AsyncClient, auth_headers: dict[str, str]):
    # When status is updated to completed in regular PUT/PATCH, completed_at should be auto-set
    res = await client.post("/tasks", json={"title": "Auto transition task"}, headers=auth_headers)
    task_id = res.json()["id"]

    update_res = await client.patch(
        f"/tasks/{task_id}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["completed_at"] is not None

    # When updated to in_progress or cancelled, completed_at should be cleared
    update_res2 = await client.patch(
        f"/tasks/{task_id}",
        json={"status": "cancelled"},
        headers=auth_headers,
    )
    assert update_res2.status_code == 200
    assert update_res2.json()["completed_at"] is None


@pytest.mark.asyncio
async def test_search_tasks(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post(
        "/tasks",
        json={"title": "Fix login authentication", "description": "High priority issue"},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "Write API docs", "description": "Cover authentication and tasks"},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "Database indexing", "description": "Add composite indexes for postgres"},
        headers=auth_headers,
    )

    # Search for 'authentication' (matches title of 1 and description of 2)
    search1 = await client.get("/tasks", params={"search": "authentication"}, headers=auth_headers)
    assert search1.status_code == 200
    assert search1.json()["total"] == 2

    # Search for 'indexing'
    search2 = await client.get("/tasks", params={"search": "indexing"}, headers=auth_headers)
    assert search2.status_code == 200
    assert search2.json()["total"] == 1
    assert search2.json()["items"][0]["title"] == "Database indexing"

    # Search with no match
    search3 = await client.get("/tasks", params={"search": "nonexistentkeyword"}, headers=auth_headers)
    assert search3.status_code == 200
    assert search3.json()["total"] == 0


@pytest.mark.asyncio
async def test_filter_overdue_and_completion(client: AsyncClient, auth_headers: dict[str, str]):
    now = datetime.now(timezone.utc)
    past_due = (now - timedelta(days=3)).isoformat()
    future_due = (now + timedelta(days=3)).isoformat()

    # 1. Overdue task (past due date, status pending)
    await client.post(
        "/tasks",
        json={"title": "Overdue Task", "due_date": past_due, "status": "pending"},
        headers=auth_headers,
    )
    # 2. Completed task with past due date (not overdue because completed)
    await client.post(
        "/tasks",
        json={"title": "Completed Past Task", "due_date": past_due, "status": "completed"},
        headers=auth_headers,
    )
    # 3. Future due task (not overdue)
    await client.post(
        "/tasks",
        json={"title": "Future Task", "due_date": future_due, "status": "in_progress"},
        headers=auth_headers,
    )

    # Filter is_overdue=true
    overdue_res = await client.get("/tasks", params={"is_overdue": True}, headers=auth_headers)
    assert overdue_res.status_code == 200
    assert overdue_res.json()["total"] == 1
    assert overdue_res.json()["items"][0]["title"] == "Overdue Task"

    # Filter is_overdue=false
    not_overdue_res = await client.get("/tasks", params={"is_overdue": False}, headers=auth_headers)
    assert not_overdue_res.status_code == 200
    assert not_overdue_res.json()["total"] == 2

    # Filter is_completed=true
    comp_res = await client.get("/tasks", params={"is_completed": True}, headers=auth_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["total"] == 1
    assert comp_res.json()["items"][0]["title"] == "Completed Past Task"

    # Filter is_completed=false
    uncomp_res = await client.get("/tasks", params={"is_completed": False}, headers=auth_headers)
    assert uncomp_res.status_code == 200
    assert uncomp_res.json()["total"] == 2


@pytest.mark.asyncio
async def test_sorting_by_priority_and_due_date(client: AsyncClient, auth_headers: dict[str, str]):
    now = datetime.now(timezone.utc)
    d1 = (now + timedelta(days=1)).isoformat()
    d2 = (now + timedelta(days=5)).isoformat()

    await client.post("/tasks", json={"title": "Low Task", "priority": "low", "due_date": d2}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Urgent Task", "priority": "urgent", "due_date": d1}, headers=auth_headers)

    # Sort priority DESC (urgent should come first)
    p_desc = await client.get("/tasks", params={"sort_by": "priority", "order": "desc"}, headers=auth_headers)
    assert p_desc.status_code == 200
    assert p_desc.json()["items"][0]["title"] == "Urgent Task"
    assert p_desc.json()["items"][1]["title"] == "Low Task"

    # Sort due_date ASC (earlier date d1 first)
    d_asc = await client.get("/tasks", params={"sort_by": "due_date", "order": "asc"}, headers=auth_headers)
    assert d_asc.status_code == 200
    assert d_asc.json()["items"][0]["title"] == "Urgent Task"
    assert d_asc.json()["items"][1]["title"] == "Low Task"


@pytest.mark.asyncio
async def test_bulk_delete_tasks(client: AsyncClient, auth_headers: dict[str, str]):
    r1 = await client.post("/tasks", json={"title": "Delete 1"}, headers=auth_headers)
    r2 = await client.post("/tasks", json={"title": "Delete 2"}, headers=auth_headers)
    r3 = await client.post("/tasks", json={"title": "Keep 3"}, headers=auth_headers)

    id1 = r1.json()["id"]
    id2 = r2.json()["id"]
    id3 = r3.json()["id"]

    bulk_res = await client.post(
        "/tasks/bulk-delete",
        json={"task_ids": [id1, id2]},
        headers=auth_headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["deleted_count"] == 2

    # Verify id1 and id2 are deleted
    assert (await client.get(f"/tasks/{id1}", headers=auth_headers)).status_code == 404
    assert (await client.get(f"/tasks/{id2}", headers=auth_headers)).status_code == 404

    # Verify id3 still exists
    assert (await client.get(f"/tasks/{id3}", headers=auth_headers)).status_code == 200


@pytest.mark.asyncio
async def test_task_ownership_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    test_user,
    other_user,
):
    """Verify that User 1 and User 2 cannot access, search, complete, or delete each other's tasks."""
    # User 1 creates a task
    res1 = await client.post(
        "/tasks",
        json={"title": "User1 Private Task", "description": "Confidential Searchable Term"},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    user1_task_id = res1.json()["id"]
    assert res1.json()["user_id"] == test_user.id

    # User 2 creates a task
    res2 = await client.post(
        "/tasks",
        json={"title": "User2 Private Task", "description": "Secret"},
        headers=other_auth_headers,
    )
    assert res2.status_code == 201
    user2_task_id = res2.json()["id"]
    assert res2.json()["user_id"] == other_user.id

    # 1. Search isolation: User 2 searching for User 1's term gets 0 results
    search_cross = await client.get("/tasks", params={"search": "Confidential"}, headers=other_auth_headers)
    assert search_cross.status_code == 200
    assert search_cross.json()["total"] == 0

    # 2. Complete / Reopen isolation: User 2 cannot complete User 1's task
    comp_cross = await client.patch(f"/tasks/{user1_task_id}/complete", headers=other_auth_headers)
    assert comp_cross.status_code == 404
    reopen_cross = await client.patch(f"/tasks/{user1_task_id}/reopen", headers=other_auth_headers)
    assert reopen_cross.status_code == 404

    # 3. Bulk delete isolation: User 2 bulk deleting User 1's task ID deletes 0 tasks
    bulk_cross = await client.post(
        "/tasks/bulk-delete",
        json={"task_ids": [user1_task_id]},
        headers=other_auth_headers,
    )
    assert bulk_cross.status_code == 200
    assert bulk_cross.json()["deleted_count"] == 0

    # Verify User 1's task still exists untouched
    verify_res = await client.get(f"/tasks/{user1_task_id}", headers=auth_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["title"] == "User1 Private Task"

    # User 1 can delete their own task
    del_own = await client.delete(f"/tasks/{user1_task_id}", headers=auth_headers)
    assert del_own.status_code == 204


@pytest.mark.asyncio
async def test_assign_task_valid_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user,
):
    res = await client.post(
        "/tasks",
        json={"title": "Team Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["assigned_to_id"] == other_user.id
    assert data["assignee"] is not None
    assert data["assignee"]["id"] == other_user.id
    assert data["assignee"]["email"] == other_user.email


@pytest.mark.asyncio
async def test_change_and_remove_assignee(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user,
):
    create_res = await client.post("/tasks", json={"title": "Flexible Assignee Task"}, headers=auth_headers)
    task_id = create_res.json()["id"]
    assert create_res.json()["assigned_to_id"] is None

    # Assign to other_user
    assign_res = await client.patch(
        f"/tasks/{task_id}",
        json={"assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_to_id"] == other_user.id
    assert assign_res.json()["assignee"]["id"] == other_user.id

    # Remove assignee
    remove_res = await client.patch(
        f"/tasks/{task_id}",
        json={"assigned_to_id": None},
        headers=auth_headers,
    )
    assert remove_res.status_code == 200
    assert remove_res.json()["assigned_to_id"] is None
    assert remove_res.json()["assignee"] is None


@pytest.mark.asyncio
async def test_assign_nonexistent_user(client: AsyncClient, auth_headers: dict[str, str]):
    res = await client.post(
        "/tasks",
        json={"title": "Bad Assign", "assigned_to_id": 99999},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "assigned user does not exist" in res.json()["detail"]


@pytest.mark.asyncio
async def test_assign_inactive_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    inactive_user,
):
    res = await client.post(
        "/tasks",
        json={"title": "Inactive Assign", "assigned_to_id": inactive_user.id},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "assigned user is inactive" in res.json()["detail"]


@pytest.mark.asyncio
async def test_assigned_user_read_access_and_mutation_forbidden(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    other_user,
):
    # Owner creates a task assigned to other_user
    create_res = await client.post(
        "/tasks",
        json={"title": "Collaborative Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    # 1. Assigned user CAN view the task
    get_res = await client.get(f"/tasks/{task_id}", headers=other_auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id
    assert get_res.json()["title"] == "Collaborative Task"

    # 2. Assigned user CANNOT modify the task (returns 403 Forbidden)
    update_res = await client.put(
        f"/tasks/{task_id}",
        json={"title": "Hijacked Title"},
        headers=other_auth_headers,
    )
    assert update_res.status_code == 403

    # 3. Assigned user CANNOT mark completed or reopen the task
    comp_res = await client.patch(f"/tasks/{task_id}/complete", headers=other_auth_headers)
    assert comp_res.status_code == 403
    reopen_res = await client.patch(f"/tasks/{task_id}/reopen", headers=other_auth_headers)
    assert reopen_res.status_code == 403

    # 4. Assigned user CANNOT attach or detach tags
    tag_res = await client.post("/tags", json={"name": "other_tag"}, headers=other_auth_headers)
    other_tag_id = tag_res.json()["id"]
    attach_res = await client.post(
        f"/tasks/{task_id}/tags",
        json={"tag_ids": [other_tag_id]},
        headers=other_auth_headers,
    )
    assert attach_res.status_code == 403

    # 5. Assigned user CANNOT delete the task
    del_res = await client.delete(f"/tasks/{task_id}", headers=other_auth_headers)
    assert del_res.status_code == 403


@pytest.mark.asyncio
async def test_combined_filters_category_and_status(client: AsyncClient, auth_headers: dict[str, str]):
    c1 = (await client.post("/categories", json={"name": "Dev"}, headers=auth_headers)).json()["id"]
    c2 = (await client.post("/categories", json={"name": "Ops"}, headers=auth_headers)).json()["id"]

    await client.post("/tasks", json={"title": "T1", "category_id": c1, "status": "pending"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T2", "category_id": c1, "status": "completed"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T3", "category_id": c2, "status": "pending"}, headers=auth_headers)

    res = await client.get("/tasks", params={"category_id": c1, "status": "pending"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "T1"


@pytest.mark.asyncio
async def test_combined_filters_tag_and_priority(client: AsyncClient, auth_headers: dict[str, str]):
    tag = (await client.post("/tags", json={"name": "infra"}, headers=auth_headers)).json()["id"]

    await client.post("/tasks", json={"title": "T1", "tag_ids": [tag], "priority": "high"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T2", "tag_ids": [tag], "priority": "low"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T3", "priority": "high"}, headers=auth_headers)

    res = await client.get("/tasks", params={"tag_id": tag, "priority": "high"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "T1"


@pytest.mark.asyncio
async def test_combined_filters_assigned_user_and_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_user,
):
    await client.post(
        "/tasks",
        json={"title": "T1", "assigned_to_id": other_user.id, "status": "in_progress"},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "T2", "assigned_to_id": other_user.id, "status": "completed"},
        headers=auth_headers,
    )
    await client.post(
        "/tasks",
        json={"title": "T3", "status": "in_progress"},
        headers=auth_headers,
    )

    res = await client.get(
        "/tasks",
        params={"assigned_to_id": other_user.id, "status": "in_progress"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "T1"


@pytest.mark.asyncio
async def test_combined_filters_category_and_tag(client: AsyncClient, auth_headers: dict[str, str]):
    c = (await client.post("/categories", json={"name": "Security"}, headers=auth_headers)).json()["id"]
    t = (await client.post("/tags", json={"name": "audit"}, headers=auth_headers)).json()["id"]

    await client.post("/tasks", json={"title": "T1", "category_id": c, "tag_ids": [t]}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T2", "category_id": c}, headers=auth_headers)
    await client.post("/tasks", json={"title": "T3", "tag_ids": [t]}, headers=auth_headers)

    res = await client.get("/tasks", params={"category_id": c, "tag_id": t}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "T1"


@pytest.mark.asyncio
async def test_combined_filters_search_category_and_tag(client: AsyncClient, auth_headers: dict[str, str]):
    c = (await client.post("/categories", json={"name": "Frontend"}, headers=auth_headers)).json()["id"]
    t = (await client.post("/tags", json={"name": "ui"}, headers=auth_headers)).json()["id"]

    await client.post("/tasks", json={"title": "Refactor Button Component", "category_id": c, "tag_ids": [t]}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Design System Docs", "category_id": c, "tag_ids": [t]}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Refactor Backend Button", "tag_ids": [t]}, headers=auth_headers)

    res = await client.get(
        "/tasks",
        params={"search": "Button", "category_id": c, "tag_id": t},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["title"] == "Refactor Button Component"


@pytest.mark.asyncio
async def test_combined_filters_sorting_and_pagination(client: AsyncClient, auth_headers: dict[str, str]):
    c = (await client.post("/categories", json={"name": "Sprint"}, headers=auth_headers)).json()["id"]

    for i in range(1, 6):
        await client.post(
            "/tasks",
            json={"title": f"Sprint Task {i}", "category_id": c, "priority": "medium"},
            headers=auth_headers,
        )

    # Page 1 (limit 2, offset 0)
    p1 = await client.get("/tasks", params={"category_id": c, "limit": 2, "offset": 0, "sort_by": "id", "order": "asc"}, headers=auth_headers)
    assert p1.status_code == 200
    assert len(p1.json()["items"]) == 2
    assert p1.json()["total"] == 5
    assert p1.json()["items"][0]["title"] == "Sprint Task 1"
    assert p1.json()["items"][1]["title"] == "Sprint Task 2"

    # Page 2 (limit 2, offset 2)
    p2 = await client.get("/tasks", params={"category_id": c, "limit": 2, "offset": 2, "sort_by": "id", "order": "asc"}, headers=auth_headers)
    assert p2.status_code == 200
    assert len(p2.json()["items"]) == 2
    assert p2.json()["items"][0]["title"] == "Sprint Task 3"
    assert p2.json()["items"][1]["title"] == "Sprint Task 4"