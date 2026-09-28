import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.post(
        "/categories",
        json={"name": "Work", "description": "Work related tasks"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Work"
    assert data["description"] == "Work related tasks"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_duplicate_category_name_same_user(client: AsyncClient, auth_headers: dict[str, str]):
    # Create first category
    res1 = await client.post(
        "/categories",
        json={"name": "Personal"},
        headers=auth_headers,
    )
    assert res1.status_code == 201

    # Attempt to create duplicate category with same name for same user
    res2 = await client.post(
        "/categories",
        json={"name": "Personal"},
        headers=auth_headers,
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_same_category_name_different_users(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    # Both users should be allowed to have their own category named "Work"
    res1 = await client.post("/categories", json={"name": "Work"}, headers=auth_headers)
    assert res1.status_code == 201

    res2 = await client.post("/categories", json={"name": "Work"}, headers=other_auth_headers)
    assert res2.status_code == 201


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/categories", json={"name": "Alpha"}, headers=auth_headers)
    await client.post("/categories", json={"name": "Beta"}, headers=auth_headers)

    res = await client.get("/categories", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    names = [c["name"] for c in data]
    assert "Alpha" in names
    assert "Beta" in names


@pytest.mark.asyncio
async def test_get_category_by_id(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post(
        "/categories",
        json={"name": "Research", "description": "AI research papers"},
        headers=auth_headers,
    )
    cat_id = create_res.json()["id"]

    get_res = await client.get(f"/categories/{cat_id}", headers=auth_headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == cat_id
    assert data["name"] == "Research"
    assert data["description"] == "AI research papers"

    # Non-existent category
    not_found = await client.get("/categories/9999", headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/categories", json={"name": "Initial"}, headers=auth_headers)
    cat_id = create_res.json()["id"]

    # PUT/PATCH update name and description
    update_res = await client.put(
        f"/categories/{cat_id}",
        json={"name": "Updated Name", "description": "New description"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Name"
    assert update_res.json()["description"] == "New description"

    # Update to an existing category name should fail with 400
    await client.post("/categories", json={"name": "OtherCat"}, headers=auth_headers)
    duplicate_update = await client.patch(
        f"/categories/{cat_id}",
        json={"name": "OtherCat"},
        headers=auth_headers,
    )
    assert duplicate_update.status_code == 400

    # Updating non-existent category
    not_found = await client.put("/categories/9999", json={"name": "X"}, headers=auth_headers)
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post("/categories", json={"name": "To Delete"}, headers=auth_headers)
    cat_id = create_res.json()["id"]

    # Delete existing
    del_res = await client.delete(f"/categories/{cat_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = await client.get(f"/categories/{cat_id}", headers=auth_headers)
    assert get_res.status_code == 404

    # Deleting non-existent category
    del_not_found = await client.delete("/categories/9999", headers=auth_headers)
    assert del_not_found.status_code == 404


@pytest.mark.asyncio
async def test_category_ownership_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    # User 1 creates a category
    res1 = await client.post("/categories", json={"name": "User 1 Secret"}, headers=auth_headers)
    u1_cat_id = res1.json()["id"]

    # User 2 listing categories should not see User 1's category
    list_u2 = await client.get("/categories", headers=other_auth_headers)
    assert list_u2.status_code == 200
    assert len(list_u2.json()) == 0

    # User 2 cannot retrieve User 1's category
    get_u2 = await client.get(f"/categories/{u1_cat_id}", headers=other_auth_headers)
    assert get_u2.status_code == 404

    # User 2 cannot update User 1's category
    update_u2 = await client.put(
        f"/categories/{u1_cat_id}",
        json={"name": "Hacked"},
        headers=other_auth_headers,
    )
    assert update_u2.status_code == 404

    # User 2 cannot delete User 1's category
    del_u2 = await client.delete(f"/categories/{u1_cat_id}", headers=other_auth_headers)
    assert del_u2.status_code == 404

    # User 2 cannot use User 1's category when creating a task
    task_res = await client.post(
        "/tasks",
        json={"title": "Unauthorized category task", "category_id": u1_cat_id},
        headers=other_auth_headers,
    )
    assert task_res.status_code == 400
    assert "Category not found or does not belong to the user" in task_res.json()["detail"]
