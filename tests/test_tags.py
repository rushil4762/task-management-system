import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/tags",
        json={"name": "backend"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "backend"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_duplicate_tag_name_same_user(client: AsyncClient, auth_headers: dict[str, str]):
    # Create first tag
    res1 = await client.post("/tags", json={"name": "frontend"}, headers=auth_headers)
    assert res1.status_code == 201

    # Attempt to create duplicate tag
    res2 = await client.post("/tags", json={"name": "frontend"}, headers=auth_headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/tags", json={"name": "urgent-fix"}, headers=auth_headers)
    await client.post("/tags", json={"name": "docs"}, headers=auth_headers)

    res = await client.get("/tags", headers=auth_headers)
    assert res.status_code == 200
    tags = res.json()
    assert len(tags) == 2
    names = [t["name"] for t in tags]
    assert "urgent-fix" in names
    assert "docs" in names


@pytest.mark.asyncio
async def test_get_tag_by_id(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tags", json={"name": "bug"}, headers=auth_headers)
    tag_id = create_res.json()["id"]

    get_res = await client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "bug"

    not_found = await client.get("/tags/9999", headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tags", json={"name": "v1"}, headers=auth_headers)
    tag_id = create_res.json()["id"]

    update_res = await client.put(f"/tags/{tag_id}", json={"name": "v2"}, headers=auth_headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "v2"

    # Updating to existing tag name
    await client.post("/tags", json={"name": "existing"}, headers=auth_headers)
    dup_res = await client.patch(f"/tags/{tag_id}", json={"name": "existing"}, headers=auth_headers)
    assert dup_res.status_code == 400

    # Non-existent tag
    not_found = await client.put("/tags/9999", json={"name": "new"}, headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/tags", json={"name": "obsolete"}, headers=auth_headers)
    tag_id = create_res.json()["id"]

    del_res = await client.delete(f"/tags/{tag_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = await client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert get_res.status_code == 404

    not_found = await client.delete("/tags/9999", headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_attach_and_remove_tags_on_task(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create tags
    tag1_res = await client.post("/tags", json={"name": "python"}, headers=auth_headers)
    tag1_id = tag1_res.json()["id"]

    tag2_res = await client.post("/tags", json={"name": "fastapi"}, headers=auth_headers)
    tag2_id = tag2_res.json()["id"]

    # 2. Create task
    task_res = await client.post("/tasks", json={"title": "Build API"}, headers=auth_headers)
    task_id = task_res.json()["id"]
    assert len(task_res.json()["tags"]) == 0

    # 3. Attach tags via dedicated endpoint
    attach_res = await client.post(
        f"/tasks/{task_id}/tags",
        json={"tag_ids": [tag1_id, tag2_id]},
        headers=auth_headers,
    )
    assert attach_res.status_code == 200
    attached_tags = attach_res.json()["tags"]
    assert len(attached_tags) == 2
    attached_tag_names = [t["name"] for t in attached_tags]
    assert "python" in attached_tag_names
    assert "fastapi" in attached_tag_names

    # 4. Duplicate tag attachment should not produce duplicate associations
    re_attach = await client.post(
        f"/tasks/{task_id}/tags",
        json={"tag_ids": [tag1_id, tag2_id]},
        headers=auth_headers,
    )
    assert re_attach.status_code == 200
    assert len(re_attach.json()["tags"]) == 2

    # 5. Remove tag1 from task
    remove_res = await client.delete(f"/tasks/{task_id}/tags/{tag1_id}", headers=auth_headers)
    assert remove_res.status_code == 200
    remaining_tags = remove_res.json()["tags"]
    assert len(remaining_tags) == 1
    assert remaining_tags[0]["name"] == "fastapi"


@pytest.mark.asyncio
async def test_create_task_with_tags_directly(client: AsyncClient, auth_headers: dict[str, str]):
    tag_res = await client.post("/tags", json={"name": "database"}, headers=auth_headers)
    tag_id = tag_res.json()["id"]

    task_res = await client.post(
        "/tasks",
        json={"title": "Optimize queries", "tag_ids": [tag_id]},
        headers=auth_headers,
    )
    assert task_res.status_code == 201
    assert len(task_res.json()["tags"]) == 1
    assert task_res.json()["tags"][0]["name"] == "database"


@pytest.mark.asyncio
async def test_filter_tasks_by_tag(client: AsyncClient, auth_headers: dict[str, str]):
    # Create two tags
    tag1_res = await client.post("/tags", json={"name": "backend"}, headers=auth_headers)
    tag1_id = tag1_res.json()["id"]

    tag2_res = await client.post("/tags", json={"name": "frontend"}, headers=auth_headers)
    tag2_id = tag2_res.json()["id"]

    # Task 1: has tag1
    await client.post("/tasks", json={"title": "Task Backend", "tag_ids": [tag1_id]}, headers=auth_headers)
    # Task 2: has tag2
    await client.post("/tasks", json={"title": "Task Frontend", "tag_ids": [tag2_id]}, headers=auth_headers)
    # Task 3: has both tags
    await client.post("/tasks", json={"title": "Fullstack Task", "tag_ids": [tag1_id, tag2_id]}, headers=auth_headers)

    # Filter by tag_id = tag1_id (should match Task 1 and Task 3)
    filter1 = await client.get("/tasks", params={"tag_id": tag1_id}, headers=auth_headers)
    assert filter1.status_code == 200
    assert filter1.json()["total"] == 2
    titles1 = [t["title"] for t in filter1.json()["items"]]
    assert "Task Backend" in titles1
    assert "Fullstack Task" in titles1

    # Filter by tag name = "frontend" (should match Task 2 and Task 3)
    filter2 = await client.get("/tasks", params={"tag": "frontend"}, headers=auth_headers)
    assert filter2.status_code == 200
    assert filter2.json()["total"] == 2
    titles2 = [t["title"] for t in filter2.json()["items"]]
    assert "Task Frontend" in titles2
    assert "Fullstack Task" in titles2


@pytest.mark.asyncio
async def test_tag_ownership_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    # User 1 creates tag
    u1_tag = await client.post("/tags", json={"name": "user1_secret_tag"}, headers=auth_headers)
    u1_tag_id = u1_tag.json()["id"]

    # User 2 listing tags cannot see User 1's tag
    u2_tags = await client.get("/tags", headers=other_auth_headers)
    assert u2_tags.status_code == 200
    assert len(u2_tags.json()) == 0

    # User 2 cannot get, update, or delete User 1's tag
    assert (await client.get(f"/tags/{u1_tag_id}", headers=other_auth_headers)).status_code == 404
    assert (await client.put(f"/tags/{u1_tag_id}", json={"name": "hack"}, headers=other_auth_headers)).status_code == 404
    assert (await client.delete(f"/tags/{u1_tag_id}", headers=other_auth_headers)).status_code == 404

    # User 2 cannot attach User 1's tag to their own task
    u2_task = await client.post("/tasks", json={"title": "User 2 Task"}, headers=other_auth_headers)
    u2_task_id = u2_task.json()["id"]

    attach_fail = await client.post(
        f"/tasks/{u2_task_id}/tags",
        json={"tag_ids": [u1_tag_id]},
        headers=other_auth_headers,
    )
    assert attach_fail.status_code == 400
    assert "One or more tags do not exist or do not belong to the user" in attach_fail.json()["detail"]

    # User 2 cannot create a task with User 1's tag
    create_fail = await client.post(
        "/tasks",
        json={"title": "User 2 Create With Alien Tag", "tag_ids": [u1_tag_id]},
        headers=other_auth_headers,
    )
    assert create_fail.status_code == 400
    assert "One or more tags do not exist or do not belong to the user" in create_fail.json()["detail"]
