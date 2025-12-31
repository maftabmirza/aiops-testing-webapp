"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.models import User, TestSuite, TestCase, Settings
from app.auth import get_password_hash, create_access_token

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database for each test function"""
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Yield session
    async with async_session_maker() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override"""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_admin=False
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create an admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        is_admin=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create an access token for the test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create an access token for the admin user"""
    return create_access_token(data={"sub": admin_user.username})


@pytest.fixture
async def test_suite(test_db: AsyncSession) -> TestSuite:
    """Create a test suite"""
    suite = TestSuite(
        name="API Tests",
        description="Test suite for API endpoints",
        category="API"
    )
    test_db.add(suite)
    await test_db.commit()
    await test_db.refresh(suite)
    return suite


@pytest.fixture
async def test_case_data(test_suite: TestSuite) -> dict:
    """Create test case data"""
    return {
        "test_id": "TC001",
        "suite_id": test_suite.id,
        "name": "Test Login Endpoint",
        "description": "Test the login endpoint with valid credentials",
        "file_path": "tests/api/test_auth.py",
        "function_name": "test_login",
        "priority": "high",
        "timeout": 30,
        "status": "active"
    }


@pytest.fixture
async def test_case_obj(test_db: AsyncSession, test_suite: TestSuite) -> TestCase:
    """Create a test case object in database"""
    test_case = TestCase(
        test_id="TC001",
        suite_id=test_suite.id,
        name="Test Login Endpoint",
        description="Test the login endpoint with valid credentials",
        file_path="tests/api/test_auth.py",
        function_name="test_login",
        priority="high",
        timeout=30,
        status="active"
    )
    test_db.add(test_case)
    await test_db.commit()
    await test_db.refresh(test_case)
    return test_case


@pytest.fixture
async def test_settings(test_db: AsyncSession) -> Settings:
    """Create test settings"""
    settings = Settings(
        aiops_url="http://localhost:8000",
        api_token="test_token",
        ssh_host="localhost",
        ssh_port=22,
        test_path="/opt/tests",
        timeout=30,
        parallel_execution=False,
        max_parallel=5,
        retry_failed=False,
        retry_count=3
    )
    test_db.add(settings)
    await test_db.commit()
    await test_db.refresh(settings)
    return settings
