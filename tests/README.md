# Test Suite

This directory contains the automated test suite for the AIOps Test Management WebApp.

## Test Coverage

The test suite covers the following areas:

### 1. Authentication Tests (`test_auth.py`)
- User login with valid/invalid credentials
- Token generation and validation
- User registration and management
- Logout functionality
- Authorization checks

### 2. Settings API Tests (`test_settings.py`)
- Retrieving system settings (with defaults)
- Saving and updating settings
- Connection testing to remote AIOps systems
- Authorization checks

### 3. Test Cases API Tests (`test_test_cases.py`)
- Creating new test cases
- Retrieving test cases (all, by suite, by status)
- Updating test cases
- Deleting test cases
- Handling duplicate test IDs
- Authorization checks

### 4. Test Runs API Tests (`test_test_runs.py`)
- Creating test runs (single case, multiple cases, full suite)
- Retrieving test runs and filtering by status/trigger
- Getting test results
- Cancelling test runs
- Authorization checks

## Running Tests

### Prerequisites

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Authentication tests
pytest tests/test_auth.py

# Settings tests
pytest tests/test_settings.py

# Test cases tests
pytest tests/test_test_cases.py

# Test runs tests
pytest tests/test_test_runs.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_auth.py::TestLogin

# Run a specific test function
pytest tests/test_auth.py::TestLogin::test_login_success
```

### Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

### Run with Coverage

```bash
pip install pytest-cov
pytest --cov=app --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

## Test Database

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) that is:
- Created fresh for each test function
- Isolated from the production database
- Automatically cleaned up after each test

## Test Fixtures

Common test fixtures are defined in `conftest.py`:
- `test_db`: Fresh database session for each test
- `client`: HTTP client with database override
- `test_user`: Regular test user
- `admin_user`: Admin test user
- `user_token`: JWT token for test user
- `admin_token`: JWT token for admin user
- `test_suite`: Sample test suite
- `test_case_data`: Sample test case data
- `test_case_obj`: Sample test case in database
- `test_settings`: Sample system settings

## Writing New Tests

To add new tests:

1. Create a new test file in `tests/` directory (must start with `test_`)
2. Import necessary fixtures from `conftest.py`
3. Organize tests into classes (optional but recommended)
4. Use `@pytest.mark.asyncio` decorator for async tests
5. Follow the existing naming conventions

Example:
```python
import pytest
from httpx import AsyncClient

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_my_endpoint(self, client: AsyncClient, user_token: str):
        response = await client.get(
            "/my-endpoint",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Use in-memory database (no external dependencies)
- Run quickly
- Are isolated and can run in parallel
- Provide clear success/failure indicators
