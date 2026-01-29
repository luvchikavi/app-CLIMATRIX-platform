"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint is accessible."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent email."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "nobody@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user, auth_headers):
    """Test getting current user profile."""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test getting profile without auth."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Test registering a new user and organization."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@company.com",
            "password": "newpassword123",
            "full_name": "New User",
            "organization_name": "New Company",
            "country_code": "US",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@company.com"
    assert data["organization"]["name"] == "New Company"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registering with existing email."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",  # Already exists
            "password": "anypassword",
            "full_name": "Duplicate User",
            "organization_name": "Another Company",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient, test_user):
    """Test forgot password endpoint (always returns success for security)."""
    response = await client.post(
        "/api/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_forgot_password_nonexistent(client: AsyncClient):
    """Test forgot password with nonexistent email (should still return success)."""
    response = await client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    # Should return 200 to prevent email enumeration
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test reset password with invalid token."""
    response = await client.post(
        "/api/auth/reset-password",
        json={"token": "invalid-token", "new_password": "newpassword123"},
    )
    assert response.status_code == 400
