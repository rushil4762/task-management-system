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


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict[str, str], test_user):
    payload = {
        "title": "Test Task",
        "description": "Testing AsyncClient with Auth",
        "status": "pending",
        "priority": "high",
    }
    response = await client.post("/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Test Task"
    assert data["description"] == "Testing AsyncClient with Auth"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
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
        json={"title": "Valid Title", "priority": "urgent"},
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
async def test_list_tasks_filtering(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/tasks", json={"title": "Task A", "status": "pending", "priority": "low"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Task B", "status": "in_progress", "priority": "high"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Task C", "status": "completed", "priority": "high"}, headers=auth_headers)

    # Filter by status
    res_status = await client.get("/tasks", params={"status": "in_progress"}, headers=auth_headers)
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total"] == 1
    assert data_status["items"][0]["title"] == "Task B"

    # Filter by priority
    res_priority = await client.get("/tasks", params={"priority": "high"}, headers=auth_headers)
    assert res_priority.status_code == 200
    data_priority = res_priority.json()
    assert data_priority["total"] == 2


@pytest.mark.asyncio
async def test_list_tasks_sorting(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/tasks", json={"title": "Alpha Task"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Beta Task"}, headers=auth_headers)

    # Sort title ASC
    asc_res = await client.get("/tasks", params={"sort_by": "title", "order": "asc"}, headers=auth_headers)
    assert asc_res.status_code == 200
    items_asc = asc_res.json()["items"]
    assert items_asc[0]["title"] == "Alpha Task"
    assert items_asc[1]["title"] == "Beta Task"

    # Sort title DESC
    desc_res = await client.get("/tasks", params={"sort_by": "title", "order": "desc"}, headers=auth_headers)
    assert desc_res.status_code == 200
    items_desc = desc_res.json()["items"]
    assert items_desc[0]["title"] == "Beta Task"
    assert items_desc[1]["title"] == "Alpha Task"

    # Invalid sort field should return 422
    invalid_sort = await client.get("/tasks", params={"sort_by": "invalid_column"}, headers=auth_headers)
    assert invalid_sort.status_code == 422


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tasks", json={"title": "Original Title"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    # PUT partial/full update
    update_res = await client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated Title", "status": "completed"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated Title"
    assert updated["status"] == "completed"

    # PATCH endpoint
    patch_res = await client.patch(
        f"/tasks/{task_id}",
        json={"priority": "high"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["priority"] == "high"
    assert patched["title"] == "Updated Title"

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
async def test_task_ownership_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    test_user,
    other_user,
):
    """Verify that User 1 and User 2 cannot access, see, edit, or delete each other's tasks."""
    # User 1 creates a task
    res1 = await client.post(
        "/tasks",
        json={"title": "User1 Private Task", "description": "Confidential"},
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

    # 1. Listing isolation: User 1 only sees User 1's tasks
    list1 = await client.get("/tasks", headers=auth_headers)
    assert list1.status_code == 200
    items1 = list1.json()["items"]
    assert all(item["user_id"] == test_user.id for item in items1)
    assert any(item["id"] == user1_task_id for item in items1)
    assert not any(item["id"] == user2_task_id for item in items1)

    # Listing isolation: User 2 only sees User 2's tasks
    list2 = await client.get("/tasks", headers=other_auth_headers)
    assert list2.status_code == 200
    items2 = list2.json()["items"]
    assert all(item["user_id"] == other_user.id for item in items2)
    assert any(item["id"] == user2_task_id for item in items2)
    assert not any(item["id"] == user1_task_id for item in items2)

    # 2. Direct GET isolation: User 2 cannot GET User 1's task
    get_cross = await client.get(f"/tasks/{user1_task_id}", headers=other_auth_headers)
    assert get_cross.status_code == 404
    assert get_cross.json()["detail"] == "Task not found"

    # User 1 cannot GET User 2's task
    get_cross2 = await client.get(f"/tasks/{user2_task_id}", headers=auth_headers)
    assert get_cross2.status_code == 404

    # 3. Update isolation: User 2 cannot PUT User 1's task
    put_cross = await client.put(
        f"/tasks/{user1_task_id}",
        json={"title": "Hacked Title"},
        headers=other_auth_headers,
    )
    assert put_cross.status_code == 404

    # User 2 cannot PATCH User 1's task
    patch_cross = await client.patch(
        f"/tasks/{user1_task_id}",
        json={"status": "completed"},
        headers=other_auth_headers,
    )
    assert patch_cross.status_code == 404

    # Verify User 1's task title was not modified
    verify_res = await client.get(f"/tasks/{user1_task_id}", headers=auth_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["title"] == "User1 Private Task"

    # 4. Delete isolation: User 2 cannot DELETE User 1's task
    del_cross = await client.delete(f"/tasks/{user1_task_id}", headers=other_auth_headers)
    assert del_cross.status_code == 404

    # Verify User 1's task still exists
    verify_res2 = await client.get(f"/tasks/{user1_task_id}", headers=auth_headers)
    assert verify_res2.status_code == 200

    # User 1 can successfully delete their own task
    del_own = await client.delete(f"/tasks/{user1_task_id}", headers=auth_headers)
    assert del_own.status_code == 204