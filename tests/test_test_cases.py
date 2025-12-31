"""
Test Cases API Tests
"""
import pytest
from httpx import AsyncClient
from app.models import TestCase, TestSuite


class TestCreateTestCase:
    """Test creating test cases"""

    @pytest.mark.asyncio
    async def test_create_test_case(
        self, client: AsyncClient, user_token: str, test_case_data: dict
    ):
        """Test creating a new test case"""
        response = await client.post(
            "/test-cases/",
            json=test_case_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["test_id"] == test_case_data["test_id"]
        assert data["name"] == test_case_data["name"]
        assert data["suite_id"] == test_case_data["suite_id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_test_case_unauthorized(self, client: AsyncClient, test_case_data: dict):
        """Test creating test case without authentication"""
        response = await client.post("/test-cases/", json=test_case_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_test_case_duplicate_test_id(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase, test_suite: TestSuite
    ):
        """Test creating test case with duplicate test_id"""
        duplicate_data = {
            "test_id": test_case_obj.test_id,  # Same as existing
            "suite_id": test_suite.id,
            "name": "Another Test",
            "description": "Test description",
            "file_path": "tests/test.py",
            "function_name": "test_func",
            "priority": "medium",
            "timeout": 30,
            "status": "active"
        }
        response = await client.post(
            "/test-cases/",
            json=duplicate_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestGetTestCases:
    """Test retrieving test cases"""

    @pytest.mark.asyncio
    async def test_get_all_test_cases(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test getting all test cases"""
        response = await client.get(
            "/test-cases/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["test_id"] == test_case_obj.test_id

    @pytest.mark.asyncio
    async def test_get_test_cases_by_suite(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase, test_suite: TestSuite
    ):
        """Test filtering test cases by suite"""
        response = await client.get(
            f"/test-cases/?suite_id={test_suite.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(tc["suite_id"] == test_suite.id for tc in data)

    @pytest.mark.asyncio
    async def test_get_test_cases_by_status(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test filtering test cases by status"""
        response = await client.get(
            "/test-cases/?status=active",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(tc["status"] == "active" for tc in data)

    @pytest.mark.asyncio
    async def test_get_test_case_by_id(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test getting a specific test case by ID"""
        response = await client.get(
            f"/test-cases/{test_case_obj.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_case_obj.id
        assert data["test_id"] == test_case_obj.test_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_test_case(self, client: AsyncClient, user_token: str):
        """Test getting a test case that doesn't exist"""
        response = await client.get(
            "/test-cases/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404


class TestUpdateTestCase:
    """Test updating test cases"""

    @pytest.mark.asyncio
    async def test_update_test_case(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test updating a test case"""
        update_data = {
            "name": "Updated Test Name",
            "description": "Updated description",
            "priority": "critical",
            "timeout": 60
        }
        response = await client.put(
            f"/test-cases/{test_case_obj.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["timeout"] == update_data["timeout"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_test_case(self, client: AsyncClient, user_token: str):
        """Test updating a test case that doesn't exist"""
        response = await client.put(
            "/test-cases/99999",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_test_case_unauthorized(self, client: AsyncClient, test_case_obj: TestCase):
        """Test updating test case without authentication"""
        response = await client.put(
            f"/test-cases/{test_case_obj.id}",
            json={"name": "Updated"}
        )
        assert response.status_code == 401


class TestDeleteTestCase:
    """Test deleting test cases"""

    @pytest.mark.asyncio
    async def test_delete_test_case(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test deleting a test case"""
        response = await client.delete(
            f"/test-cases/{test_case_obj.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200

        # Verify deletion
        get_response = await client.get(
            f"/test-cases/{test_case_obj.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_test_case(self, client: AsyncClient, user_token: str):
        """Test deleting a test case that doesn't exist"""
        response = await client.delete(
            "/test-cases/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_test_case_unauthorized(self, client: AsyncClient, test_case_obj: TestCase):
        """Test deleting test case without authentication"""
        response = await client.delete(f"/test-cases/{test_case_obj.id}")
        assert response.status_code == 401
