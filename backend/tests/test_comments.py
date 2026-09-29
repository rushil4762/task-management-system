import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_comment_by_owner(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Comment Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "First comment by task owner"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["task_id"] == task_id
    assert data["content"] == "First comment by task owner"
    assert "id" in data
    assert "user" in data
    assert data["user"]["email"] == "testuser@example.com"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_comment_by_assignee(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    other_user,
):
    # Owner creates task assigned to other_user
    task_res = await client.post(
        "/tasks",
        json={"title": "Assigned Comment Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # Assignee can add a comment
    res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Looking into this now"},
        headers=other_auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["task_id"] == task_id
    assert data["content"] == "Looking into this now"
    assert data["user"]["id"] == other_user.id
    assert data["user"]["email"] == other_user.email


@pytest.mark.asyncio
async def test_list_comments_for_task(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    other_user,
):
    task_res = await client.post(
        "/tasks",
        json={"title": "Threaded Discussion", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # Owner adds a comment
    await client.post(f"/tasks/{task_id}/comments", json={"content": "Initial instructions"}, headers=auth_headers)
    # Assignee adds a comment
    await client.post(f"/tasks/{task_id}/comments", json={"content": "Acknowledged"}, headers=other_auth_headers)

    # Both owner and assignee can list comments
    owner_list = await client.get(f"/tasks/{task_id}/comments", headers=auth_headers)
    assert owner_list.status_code == 200
    comments = owner_list.json()
    assert len(comments) == 2
    assert comments[0]["content"] == "Initial instructions"
    assert comments[1]["content"] == "Acknowledged"

    assignee_list = await client.get(f"/tasks/{task_id}/comments", headers=other_auth_headers)
    assert assignee_list.status_code == 200
    assert len(assignee_list.json()) == 2


@pytest.mark.asyncio
async def test_edit_own_comment(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Editable Comment Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    comm_res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Original comment"},
        headers=auth_headers,
    )
    comment_id = comm_res.json()["id"]

    # PUT edit
    put_res = await client.put(
        f"/comments/{comment_id}",
        json={"content": "Edited comment via PUT"},
        headers=auth_headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["content"] == "Edited comment via PUT"

    # PATCH edit
    patch_res = await client.patch(
        f"/comments/{comment_id}",
        json={"content": "Edited comment via PATCH"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["content"] == "Edited comment via PATCH"


@pytest.mark.asyncio
async def test_delete_own_comment(client: AsyncClient, auth_headers: dict[str, str]):
    task_res = await client.post("/tasks", json={"title": "Deletable Comment Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    comm_res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Will be deleted"},
        headers=auth_headers,
    )
    comment_id = comm_res.json()["id"]

    del_res = await client.delete(f"/comments/{comment_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify comment no longer in task comments list
    list_res = await client.get(f"/tasks/{task_id}/comments", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


@pytest.mark.asyncio
async def test_comment_ownership_cannot_edit_or_delete_others_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
    other_user,
):
    # Task created by user 1, assigned to user 2
    task_res = await client.post(
        "/tasks",
        json={"title": "Collab Task", "assigned_to_id": other_user.id},
        headers=auth_headers,
    )
    task_id = task_res.json()["id"]

    # User 1 posts comment 1
    c1_res = await client.post(f"/tasks/{task_id}/comments", json={"content": "User 1 note"}, headers=auth_headers)
    c1_id = c1_res.json()["id"]

    # User 2 cannot edit User 1's comment
    edit_cross = await client.put(f"/comments/{c1_id}", json={"content": "Tampered"}, headers=other_auth_headers)
    assert edit_cross.status_code == 403
    assert "Not authorized" in edit_cross.json()["detail"]

    # User 2 cannot delete User 1's comment
    del_cross = await client.delete(f"/comments/{c1_id}", headers=other_auth_headers)
    assert del_cross.status_code == 403
    assert "Not authorized" in del_cross.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_view_or_post_comments(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    # Private task for User 1 (not assigned to User 2)
    task_res = await client.post("/tasks", json={"title": "Private Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # User 2 cannot post comments to User 1's private task
    post_unauth = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Intruder comment"},
        headers=other_auth_headers,
    )
    assert post_unauth.status_code == 404

    # User 2 cannot view comments of User 1's private task
    get_unauth = await client.get(f"/tasks/{task_id}/comments", headers=other_auth_headers)
    assert get_unauth.status_code == 404


@pytest.mark.asyncio
async def test_comment_content_validation_rejects_empty(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    task_res = await client.post("/tasks", json={"title": "Validation Task"}, headers=auth_headers)
    task_id = task_res.json()["id"]

    # Empty content
    empty_res = await client.post(f"/tasks/{task_id}/comments", json={"content": ""}, headers=auth_headers)
    assert empty_res.status_code == 422

    # Whitespace-only content
    blank_res = await client.post(f"/tasks/{task_id}/comments", json={"content": "   \n  "}, headers=auth_headers)
    assert blank_res.status_code == 422


@pytest.mark.asyncio
async def test_comment_not_found(client: AsyncClient, auth_headers: dict[str, str]):
    assert (await client.put("/comments/9999", json={"content": "New"}, headers=auth_headers)).status_code == 404
    assert (await client.delete("/comments/9999", headers=auth_headers)).status_code == 404
