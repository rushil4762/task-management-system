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
async def test_create_task(client: AsyncClient):
    payload = {
        "title": "Test Task",
        "description": "Testing AsyncClient",
        "status": "pending",
        "priority": "high",
    }
    response = await client.post("/tasks", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Test Task"
    assert data["description"] == "Testing AsyncClient"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_task_validation_errors(client: AsyncClient):
    # Empty title
    response = await client.post("/tasks", json={"title": ""})
    assert response.status_code == 422

    # Whitespace-only title
    response = await client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422

    # Invalid status
    response = await client.post("/tasks", json={"title": "Valid Title", "status": "unknown_status"})
    assert response.status_code == 422

    # Invalid priority
    response = await client.post("/tasks", json={"title": "Valid Title", "priority": "urgent"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_by_id(client: AsyncClient):
    create_res = await client.post(
        "/tasks",
        json={"title": "Fetchable Task", "priority": "low"},
    )
    task_id = create_res.json()["id"]

    # Successful retrieval
    get_res = await client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Fetchable Task"

    # Non-existent task ID
    not_found = await client.get("/tasks/99999")
    assert not_found.status_code == 404
    assert not_found.json()["detail"] == "Task not found"

    # Invalid task ID (path validation ge=1)
    invalid_id = await client.get("/tasks/0")
    assert invalid_id.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient):
    # Create 5 tasks
    for i in range(5):
        await client.post("/tasks", json={"title": f"Task {i}"})

    # Page 1 (limit 2, offset 0)
    page1 = await client.get("/tasks", params={"limit": 2, "offset": 0})
    assert page1.status_code == 200
    data1 = page1.json()
    assert len(data1["items"]) == 2
    assert data1["total"] == 5
    assert data1["limit"] == 2
    assert data1["offset"] == 0

    # Page 2 (limit 2, offset 2)
    page2 = await client.get("/tasks", params={"limit": 2, "offset": 2})
    assert page2.status_code == 200
    data2 = page2.json()
    assert len(data2["items"]) == 2
    assert data2["total"] == 5
    assert data2["offset"] == 2


@pytest.mark.asyncio
async def test_list_tasks_filtering(client: AsyncClient):
    await client.post("/tasks", json={"title": "Task A", "status": "pending", "priority": "low"})
    await client.post("/tasks", json={"title": "Task B", "status": "in_progress", "priority": "high"})
    await client.post("/tasks", json={"title": "Task C", "status": "completed", "priority": "high"})

    # Filter by status
    res_status = await client.get("/tasks", params={"status": "in_progress"})
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total"] == 1
    assert data_status["items"][0]["title"] == "Task B"

    # Filter by priority
    res_priority = await client.get("/tasks", params={"priority": "high"})
    assert res_priority.status_code == 200
    data_priority = res_priority.json()
    assert data_priority["total"] == 2


@pytest.mark.asyncio
async def test_list_tasks_sorting(client: AsyncClient):
    await client.post("/tasks", json={"title": "Alpha Task"})
    await client.post("/tasks", json={"title": "Beta Task"})

    # Sort title ASC
    asc_res = await client.get("/tasks", params={"sort_by": "title", "order": "asc"})
    assert asc_res.status_code == 200
    items_asc = asc_res.json()["items"]
    assert items_asc[0]["title"] == "Alpha Task"
    assert items_asc[1]["title"] == "Beta Task"

    # Sort title DESC
    desc_res = await client.get("/tasks", params={"sort_by": "title", "order": "desc"})
    assert desc_res.status_code == 200
    items_desc = desc_res.json()["items"]
    assert items_desc[0]["title"] == "Beta Task"
    assert items_desc[1]["title"] == "Alpha Task"

    # Invalid sort field should return 422
    invalid_sort = await client.get("/tasks", params={"sort_by": "invalid_column"})
    assert invalid_sort.status_code == 422


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    create_res = await client.post("/tasks", json={"title": "Original Title"})
    task_id = create_res.json()["id"]

    # PUT partial/full update
    update_res = await client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated Title", "status": "completed"},
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated Title"
    assert updated["status"] == "completed"

    # PATCH endpoint
    patch_res = await client.patch(
        f"/tasks/{task_id}",
        json={"priority": "high"},
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["priority"] == "high"
    assert patched["title"] == "Updated Title"

    # Updating non-existent task
    not_found = await client.put("/tasks/9999", json={"title": "New"})
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    create_res = await client.post("/tasks", json={"title": "Task to Delete"})
    task_id = create_res.json()["id"]

    # Delete existing task
    delete_res = await client.delete(f"/tasks/{task_id}")
    assert delete_res.status_code == 204

    # Verify task is deleted
    get_res = await client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 404

    # Deleting non-existent task
    del_not_found = await client.delete("/tasks/9999")
    assert del_not_found.status_code == 404