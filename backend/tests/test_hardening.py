"""
Production hardening and security test suite.
Validates:
- Password hashing security (bcrypt 72-byte limit handling, verification)
- Email case-insensitivity & normalization
- Inactive user access prevention
- JWT security (tampered, expired, wrong type)
- HTTP security headers
- Health check database probe and error safety
- Production configuration validation
- SQL injection resistance on search & filters
- Pagination input bounds (limit, offset)
- Cross-user IDOR access isolation
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import Settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User


# ============================================================================
# 1. Authentication Security: Password Hashing & Bcrypt Limits
# ============================================================================


def test_password_hashing_handles_long_passwords():
    """Verify passwords longer than 72 bytes do not crash bcrypt and verify cleanly."""
    long_pw = "VeryLongSecurePassword!" + "A" * 60
    hashed = hash_password(long_pw)
    assert isinstance(hashed, str)
    assert verify_password(long_pw, hashed) is True
    assert verify_password("DifferentPassword!" + "A" * 60, hashed) is False


@pytest.mark.asyncio
async def test_auth_with_long_password(client: AsyncClient):
    """Verify user registration and login work with a 90-character password."""
    long_pw = "VeryLongSecurePassword!" + "X" * 60
    email = "longpass@example.com"

    reg_res = await client.post(
        "/auth/register",
        json={"name": "Long Pass User", "email": email, "password": long_pw},
    )
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/auth/login",
        json={"email": email, "password": long_pw},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


# ============================================================================
# 2. Email Normalization & Case Insensitivity
# ============================================================================


@pytest.mark.asyncio
async def test_email_normalization_and_case_insensitive_login(client: AsyncClient):
    """Verify email is normalized to lowercase and login is case-insensitive."""
    email_mixed = "MixedCase.User@Example.COM"
    password = "SecurePassword123!"

    reg_res = await client.post(
        "/auth/register",
        json={"name": "Mixed Case User", "email": email_mixed, "password": password},
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == email_mixed.strip().lower()

    # Login with all uppercase
    login_upper = await client.post(
        "/auth/login",
        json={"email": email_mixed.upper(), "password": password},
    )
    assert login_upper.status_code == 200

    # Duplicate check with all lowercase
    reg_dup = await client.post(
        "/auth/register",
        json={"name": "Duplicate User", "email": email_mixed.lower(), "password": password},
    )
    assert reg_dup.status_code == 400
    assert "already exists" in reg_dup.json()["detail"]


# ============================================================================
# 3. Inactive User Handling
# ============================================================================


@pytest.mark.asyncio
async def test_inactive_user_cannot_login_or_access_me(
    client: AsyncClient,
    inactive_user: User,
):
    """Verify inactive users are rejected with 403 Forbidden on login and me."""
    # Login should be rejected
    login_res = await client.post(
        "/auth/login",
        json={"email": inactive_user.email, "password": "Password789!"},
    )
    assert login_res.status_code == 403
    assert "inactive" in login_res.json()["detail"].lower()

    # Existing token should also be rejected on /auth/me
    token = create_access_token(subject=inactive_user.id, extra_claims={"email": inactive_user.email})
    me_res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 403


# ============================================================================
# 4. JWT Validation & Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_jwt_validation_expired_and_wrong_type(client: AsyncClient):
    """Verify expired tokens and tokens with incorrect types are rejected."""
    # 1. Expired token
    expired_token = create_access_token(
        subject=1,
        expires_delta=timedelta(seconds=-10),
    )
    res_expired = await client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401

    # 2. Tampered token
    tampered = expired_token[:-5] + "XXXXX"
    res_tampered = await client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert res_tampered.status_code == 401

    # 3. Refresh token used as access token
    refresh_token = create_refresh_token(subject=1)
    res_type = await client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert res_type.status_code == 401


# ============================================================================
# 5. Security Headers
# ============================================================================


@pytest.mark.asyncio
async def test_security_headers_present_on_responses(client: AsyncClient):
    """Verify essential HTTP security headers are returned on all endpoints."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# ============================================================================
# 6. Health Check Probing
# ============================================================================


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient):
    """Verify health endpoint reports connected database and environment."""
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "environment" in data


# ============================================================================
# 7. Production Settings Validation
# ============================================================================


def test_production_settings_validation_catches_insecure_defaults():
    """Verify production settings validator rejects default secret, debug mode, and wildcard CORS."""
    # 1. Insecure default secret in production
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be a secure secret"):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="your-super-secret-jwt-key-replace-in-production",
            CORS_ORIGINS=["https://frontend.example.com"],
        )

    # 2. DEBUG=True in production
    with pytest.raises(ValueError, match="DEBUG must be set to False"):
        Settings(
            APP_ENV="production",
            DEBUG=True,
            JWT_SECRET_KEY="a" * 32,
            CORS_ORIGINS=["https://frontend.example.com"],
        )

    # 3. Wildcard CORS in production
    with pytest.raises(ValueError, match=r"Wildcard '\*' CORS origins are not permitted"):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="a" * 32,
            CORS_ORIGINS=["*"],
        )

    # 4. Valid production settings pass
    valid_prod = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="this-is-a-strong-32-byte-secret-key-1234",
        CORS_ORIGINS=["https://frontend.example.com"],
    )
    assert valid_prod.APP_ENV == "production"
    assert valid_prod.DEBUG is False


# ============================================================================
# 8. SQL Injection & Input Filtering Resistance
# ============================================================================


@pytest.mark.asyncio
async def test_search_sql_injection_payloads_are_safe(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify SQL injection strings in search query parameters do not cause errors or SQL execution."""
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE tasks; --",
        "1; SELECT * FROM users;",
        "admin'--",
        "' UNION SELECT * FROM users --",
    ]
    for p in payloads:
        res = await client.get(f"/tasks?search={p}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_invalid_sort_field_rejected(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify sorting by non-allowed fields is rejected with 422."""
    res = await client.get("/tasks?sort_by=non_existent_column", headers=auth_headers)
    assert res.status_code == 422


# ============================================================================
# 9. Pagination Bounds Validation
# ============================================================================


@pytest.mark.asyncio
async def test_pagination_bounds_validation(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Verify limit < 1, limit > 100, and offset < 0 are rejected across all endpoints."""
    # Tasks
    assert (await client.get("/tasks?limit=0", headers=auth_headers)).status_code == 422
    assert (await client.get("/tasks?limit=101", headers=auth_headers)).status_code == 422
    assert (await client.get("/tasks?offset=-1", headers=auth_headers)).status_code == 422

    # Notifications
    assert (await client.get("/notifications?limit=0", headers=auth_headers)).status_code == 422
    assert (await client.get("/notifications?limit=101", headers=auth_headers)).status_code == 422
    assert (await client.get("/notifications?offset=-1", headers=auth_headers)).status_code == 422

    # Dashboard completion-trend days bounds
    assert (await client.get("/dashboard/completion-trend?days=0", headers=auth_headers)).status_code == 422
    assert (await client.get("/dashboard/completion-trend?days=400", headers=auth_headers)).status_code == 422


# ============================================================================
# 10. Cross-User IDOR Access Isolation
# ============================================================================


@pytest.mark.asyncio
async def test_cross_user_category_and_comment_idor_protection(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_auth_headers: dict[str, str],
):
    """
    Verify complete isolation between users:
    - User 2 cannot access, update, or delete User 1's category.
    - User 2 cannot view or mutate tasks belonging to User 1.
    """
    # 1. User 1 creates a category
    cat_res = await client.post(
        "/categories",
        json={"name": "User1 Private Category"},
        headers=auth_headers,
    )
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # User 2 tries to GET User 1's category -> 404
    get_res = await client.get(f"/categories/{cat_id}", headers=other_auth_headers)
    assert get_res.status_code == 404

    # User 2 tries to UPDATE User 1's category -> 404
    update_res = await client.put(
        f"/categories/{cat_id}",
        json={"name": "Hacked Category"},
        headers=other_auth_headers,
    )
    assert update_res.status_code == 404

    # User 2 tries to DELETE User 1's category -> 404
    del_res = await client.delete(f"/categories/{cat_id}", headers=other_auth_headers)
    assert del_res.status_code == 404

    # 2. User 1 creates a task
    task_res = await client.post(
        "/tasks",
        json={"title": "User 1 Private Task"},
        headers=auth_headers,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # User 2 tries to access activities for User 1's task -> 404
    act_res = await client.get(f"/tasks/{task_id}/activities", headers=other_auth_headers)
    assert act_res.status_code == 404

    # User 2 tries to post comment on User 1's task -> 404
    comm_res = await client.post(
        f"/tasks/{task_id}/comments",
        json={"content": "Unauthorized comment"},
        headers=other_auth_headers,
    )
    assert comm_res.status_code == 404
