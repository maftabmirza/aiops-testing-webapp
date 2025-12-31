"""
Test Runs API Tests
"""
import pytest
from httpx import AsyncClient
from app.models import TestCase, TestSuite


class TestCreateTestRun:
    """Test creating test runs"""

    @pytest.mark.asyncio
    async def test_create_test_run_single_case(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test creating a test run for a single test case"""
        response = await client.post(
            "/test-runs/",
            json={
                "test_case_ids": [test_case_obj.id],
                "trigger": "manual"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["trigger"] == "manual"
        assert data["total_tests"] == 1
        assert data["status"] in ["pending", "running"]

    @pytest.mark.asyncio
    async def test_create_test_run_suite(
        self, client: AsyncClient, user_token: str, test_suite: TestSuite, test_case_obj: TestCase
    ):
        """Test creating a test run for an entire suite"""
        response = await client.post(
            f"/test-runs/suite/{test_suite.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["trigger"] == "manual"
        assert data["total_tests"] >= 1

    @pytest.mark.asyncio
    async def test_create_test_run_empty_list(self, client: AsyncClient, user_token: str):
        """Test creating a test run with empty test case list"""
        response = await client.post(
            "/test-runs/",
            json={
                "test_case_ids": [],
                "trigger": "manual"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_test_run_nonexistent_suite(self, client: AsyncClient, user_token: str):
        """Test creating a test run for a non-existent suite"""
        response = await client.post(
            "/test-runs/suite/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_test_run_unauthorized(self, client: AsyncClient, test_case_obj: TestCase):
        """Test creating test run without authentication"""
        response = await client.post(
            "/test-runs/",
            json={"test_case_ids": [test_case_obj.id], "trigger": "manual"}
        )
        assert response.status_code == 401


class TestGetTestRuns:
    """Test retrieving test runs"""

    @pytest.mark.asyncio
    async def test_get_all_test_runs(self, client: AsyncClient, user_token: str):
        """Test getting all test runs"""
        response = await client.get(
            "/test-runs/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_test_runs_by_status(self, client: AsyncClient, user_token: str):
        """Test filtering test runs by status"""
        response = await client.get(
            "/test-runs/?status=completed",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_test_runs_by_trigger(self, client: AsyncClient, user_token: str):
        """Test filtering test runs by trigger"""
        response = await client.get(
            "/test-runs/?trigger=manual",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_test_run_by_id(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test getting a specific test run by ID"""
        # First create a test run
        create_response = await client.post(
            "/test-runs/",
            json={"test_case_ids": [test_case_obj.id], "trigger": "manual"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert create_response.status_code == 200
        test_run_id = create_response.json()["id"]

        # Get the test run
        response = await client.get(
            f"/test-runs/{test_run_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_run_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_test_run(self, client: AsyncClient, user_token: str):
        """Test getting a test run that doesn't exist"""
        response = await client.get(
            "/test-runs/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_test_runs_unauthorized(self, client: AsyncClient):
        """Test getting test runs without authentication"""
        response = await client.get("/test-runs/")
        assert response.status_code == 401


class TestGetTestResults:
    """Test retrieving test results"""

    @pytest.mark.asyncio
    async def test_get_results_for_run(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test getting results for a specific test run"""
        # Create a test run
        create_response = await client.post(
            "/test-runs/",
            json={"test_case_ids": [test_case_obj.id], "trigger": "manual"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        test_run_id = create_response.json()["id"]

        # Get results
        response = await client.get(
            f"/test-runs/{test_run_id}/results",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_results_for_nonexistent_run(self, client: AsyncClient, user_token: str):
        """Test getting results for a non-existent test run"""
        response = await client.get(
            "/test-runs/99999/results",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404


class TestCancelTestRun:
    """Test cancelling test runs"""

    @pytest.mark.asyncio
    async def test_cancel_test_run(
        self, client: AsyncClient, user_token: str, test_case_obj: TestCase
    ):
        """Test cancelling a running test run"""
        # Create a test run
        create_response = await client.post(
            "/test-runs/",
            json={"test_case_ids": [test_case_obj.id], "trigger": "manual"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        test_run_id = create_response.json()["id"]

        # Cancel the test run
        response = await client.post(
            f"/test-runs/{test_run_id}/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Should either succeed or fail if already completed
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_test_run(self, client: AsyncClient, user_token: str):
        """Test cancelling a non-existent test run"""
        response = await client.post(
            "/test-runs/99999/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_test_run_unauthorized(self, client: AsyncClient):
        """Test cancelling test run without authentication"""
        response = await client.post("/test-runs/1/cancel")
        assert response.status_code == 401
