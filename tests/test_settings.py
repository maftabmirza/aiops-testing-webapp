"""
Settings API Tests
"""
import pytest
from httpx import AsyncClient
from app.models import Settings


class TestGetSettings:
    """Test retrieving settings"""

    @pytest.mark.asyncio
    async def test_get_settings_with_data(
        self, client: AsyncClient, user_token: str, test_settings: Settings
    ):
        """Test getting settings when settings exist"""
        response = await client.get(
            "/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["aiops_url"] == test_settings.aiops_url
        assert data["ssh_host"] == test_settings.ssh_host
        assert data["ssh_port"] == test_settings.ssh_port
        assert data["timeout"] == test_settings.timeout
        assert data["parallel_execution"] == test_settings.parallel_execution
        assert data["max_parallel"] == test_settings.max_parallel

    @pytest.mark.asyncio
    async def test_get_settings_default(self, client: AsyncClient, user_token: str):
        """Test getting settings when no settings exist (should return defaults)"""
        response = await client.get(
            "/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["aiops_url"] == ""
        assert data["ssh_port"] == 22
        assert data["timeout"] == 30
        assert data["parallel_execution"] is False
        assert data["max_parallel"] == 5

    @pytest.mark.asyncio
    async def test_get_settings_unauthorized(self, client: AsyncClient):
        """Test getting settings without authentication"""
        response = await client.get("/api/settings")
        assert response.status_code == 401


class TestSaveSettings:
    """Test saving settings"""

    @pytest.mark.asyncio
    async def test_save_new_settings(self, client: AsyncClient, user_token: str):
        """Test saving new settings"""
        settings_data = {
            "aiops_url": "http://aiops.example.com",
            "api_token": "new_token_123",
            "ssh_host": "aiops.example.com",
            "ssh_port": 2222,
            "test_path": "/var/tests",
            "timeout": 60,
            "parallel_execution": True,
            "max_parallel": 10,
            "retry_failed": True,
            "retry_count": 5
        }

        response = await client.post(
            "/api/settings",
            json=settings_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

        # Verify settings were saved
        get_response = await client.get(
            "/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == 200
        saved_data = get_response.json()
        assert saved_data["aiops_url"] == settings_data["aiops_url"]
        assert saved_data["ssh_port"] == settings_data["ssh_port"]
        assert saved_data["parallel_execution"] == settings_data["parallel_execution"]

    @pytest.mark.asyncio
    async def test_update_existing_settings(
        self, client: AsyncClient, user_token: str, test_settings: Settings
    ):
        """Test updating existing settings"""
        updated_data = {
            "aiops_url": "http://new-aiops.example.com",
            "api_token": test_settings.api_token,
            "ssh_host": "new-host",
            "ssh_port": 3333,
            "test_path": test_settings.test_path,
            "timeout": 90,
            "parallel_execution": True,
            "max_parallel": 15,
            "retry_failed": True,
            "retry_count": 3
        }

        response = await client.post(
            "/api/settings",
            json=updated_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200

        # Verify settings were updated
        get_response = await client.get(
            "/api/settings",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        saved_data = get_response.json()
        assert saved_data["aiops_url"] == updated_data["aiops_url"]
        assert saved_data["ssh_host"] == updated_data["ssh_host"]
        assert saved_data["timeout"] == updated_data["timeout"]

    @pytest.mark.asyncio
    async def test_save_settings_unauthorized(self, client: AsyncClient):
        """Test saving settings without authentication"""
        response = await client.post(
            "/api/settings",
            json={"aiops_url": "http://test.com"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_settings_partial_data(self, client: AsyncClient, user_token: str):
        """Test saving settings with partial data (should use None/defaults)"""
        settings_data = {
            "aiops_url": "http://minimal.example.com",
            "timeout": 45,
            "parallel_execution": False,
            "max_parallel": 5,
            "retry_failed": False,
            "retry_count": 3
        }

        response = await client.post(
            "/api/settings",
            json=settings_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


class TestConnectionTest:
    """Test connection testing"""

    @pytest.mark.asyncio
    async def test_test_connection_no_url(self, client: AsyncClient, user_token: str):
        """Test connection without URL"""
        response = await client.post(
            "/api/settings/test-connection",
            json={"url": "", "token": None},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400
        assert "URL is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_test_connection_unauthorized(self, client: AsyncClient):
        """Test connection without authentication"""
        response = await client.post(
            "/api/settings/test-connection",
            json={"url": "http://test.com", "token": None}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_test_connection_invalid_url(self, client: AsyncClient, user_token: str):
        """Test connection with invalid/unreachable URL"""
        response = await client.post(
            "/api/settings/test-connection",
            json={"url": "http://nonexistent-domain-12345.com", "token": None},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Should return error (503 or 500)
        assert response.status_code in [503, 500, 504]
