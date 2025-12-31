"""
Test Suites API - Manage test suite groups
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import TestSuite, TestCase, User
from app.api.auth import get_current_user

router = APIRouter(prefix="/test-suites", tags=["test_suites"])


# Pydantic Schemas
class TestSuiteResponse(BaseModel):
    """Response schema for a test suite"""
    id: int
    name: str
    description: str | None
    category: str
    test_count: int = 0

    class Config:
        from_attributes = True


@router.get("/list")
async def list_test_suites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of all test suites with test counts
    """
    # Query all test suites
    query = select(TestSuite).order_by(TestSuite.name)
    result = await db.execute(query)
    suites = result.scalars().all()

    # Get test counts for each suite
    response = []
    for suite in suites:
        # Count tests in this suite
        count_query = select(func.count(TestCase.id)).where(TestCase.suite_id == suite.id)
        count_result = await db.execute(count_query)
        test_count = count_result.scalar() or 0

        response.append({
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "category": suite.category,
            "test_count": test_count
        })

    return response


@router.get("/{suite_id}")
async def get_test_suite(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific test suite by ID
    """
    query = select(TestSuite).where(TestSuite.id == suite_id)
    result = await db.execute(query)
    suite = result.scalar_one_or_none()

    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Get test count
    count_query = select(func.count(TestCase.id)).where(TestCase.suite_id == suite.id)
    count_result = await db.execute(count_query)
    test_count = count_result.scalar() or 0

    return {
        "id": suite.id,
        "name": suite.name,
        "description": suite.description,
        "category": suite.category,
        "enabled": suite.enabled,
        "test_count": test_count
    }


@router.get("/{suite_id}/tests")
async def get_suite_tests(
    suite_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[int]:
    """
    Get all test case IDs for a specific suite
    """
    query = select(TestCase.id).where(TestCase.suite_id == suite_id)
    result = await db.execute(query)
    test_ids = [row[0] for row in result.all()]

    return test_ids
