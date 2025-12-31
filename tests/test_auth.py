"""
Authentication API Tests
"""
import pytest
from httpx import AsyncClient
from app.models import User


class TestLogin:
    """Test login functionality"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials"""
        response = await client.post(
            "/api/auth/token",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password"""
        response = await client.post(
            "/api/auth/token",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user"""
        response = await client.post(
            "/api/auth/token",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        assert response.status_code == 401


class TestUserManagement:
    """Test user management endpoints"""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, user_token: str, test_user: User):
        """Test getting current user information"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data  # Should not expose password

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestUserRegistration:
    """Test user registration"""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient, admin_token: str):
        """Test user registration with admin privileges"""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(
        self, client: AsyncClient, admin_token: str, test_user: User
    ):
        """Test registration with duplicate username"""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "email": "another@example.com",
                "password": "password",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, client: AsyncClient, admin_token: str, test_user: User
    ):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "anotheruser",
                "email": test_user.email,
                "password": "password",
                "is_admin": False
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestLogout:
    """Test logout functionality"""

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, user_token: str):
        """Test user logout"""
        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()
