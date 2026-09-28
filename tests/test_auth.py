import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "name": "Alice Wonder",
        "email": "alice@example.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Alice Wonder"
    assert data["email"] == "alice@example.com"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "name": "Bob Builder",
        "email": "bob@example.com",
        "password": "Password123!",
    }
    # First registration
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Duplicate registration
    res2 = await client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_validation_errors(client: AsyncClient):
    # Short password (<8 chars)
    res = await client.post(
        "/auth/register",
        json={"name": "Shorty", "email": "short@example.com", "password": "short"},
    )
    assert res.status_code == 422

    # Invalid email format
    res = await client.post(
        "/auth/register",
        json={"name": "Bad Email", "email": "not-an-email", "password": "Password123!"},
    )
    assert res.status_code == 422

    # Blank name
    res = await client.post(
        "/auth/register",
        json={"name": "   ", "email": "blank@example.com", "password": "Password123!"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Register first
    await client.post(
        "/auth/register",
        json={"name": "Charlie", "email": "charlie@example.com", "password": "Password123!"},
    )

    # Login
    response = await client.post(
        "/auth/login",
        json={"email": "charlie@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"name": "Diana", "email": "diana@example.com", "password": "CorrectPassword123!"},
    )

    response = await client.post(
        "/auth/login",
        json={"email": "diana@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient, auth_headers: dict[str, str], test_user):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


@pytest.mark.asyncio
async def test_unauthenticated_me_access(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient):
    # Register & Login
    await client.post(
        "/auth/register",
        json={"name": "Frank", "email": "frank@example.com", "password": "Password123!"},
    )
    login_res = await client.post(
        "/auth/login",
        json={"email": "frank@example.com", "password": "Password123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Use refresh token
    refresh_res = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # Use the newly obtained access token to access /auth/me
    headers = {"Authorization": f"Bearer {new_data['access_token']}"}
    me_res = await client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "frank@example.com"


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    res = await client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )
    assert res.status_code == 401
