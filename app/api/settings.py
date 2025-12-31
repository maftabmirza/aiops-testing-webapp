"""
Settings API - Manage system configuration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from pydantic import BaseModel, Field
import httpx

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os

from app.database import get_db
from app.models import Settings, User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])
web_router = APIRouter(prefix="/settings", tags=["settings_web"])

# Get the templates directory
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


# Pydantic Schemas
class SettingsUpdate(BaseModel):
    """Schema for updating settings"""
    aiops_url: str | None = None
    api_token: str | None = None
    ssh_host: str | None = None
    ssh_port: int | None = 22
    test_path: str | None = None
    timeout: int | None = 30
    parallel_execution: bool = False
    max_parallel: int = 5
    retry_failed: bool = False
    retry_count: int = 3


class ConnectionTestRequest(BaseModel):
    """Schema for testing connection"""
    url: str
    token: str | None = None


@web_router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Render the settings HTML page
    """
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "current_user": current_user
    })


@router.get("")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current system settings
    """
    # Get the first (and only) settings record
    query = select(Settings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Return default settings if none exist
        return {
            "aiops_url": "",
            "api_token": "",
            "ssh_host": "",
            "ssh_port": 22,
            "test_path": "",
            "timeout": 30,
            "parallel_execution": False,
            "max_parallel": 5,
            "retry_failed": False,
            "retry_count": 3
        }

    return {
        "aiops_url": settings.aiops_url or "",
        "api_token": settings.api_token or "",
        "ssh_host": settings.ssh_host or "",
        "ssh_port": settings.ssh_port or 22,
        "test_path": settings.test_path or "",
        "timeout": settings.timeout or 30,
        "parallel_execution": settings.parallel_execution,
        "max_parallel": settings.max_parallel,
        "retry_failed": settings.retry_failed,
        "retry_count": settings.retry_count
    }


@router.post("")
async def save_settings(
    settings_data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Save system settings
    """
    # Get existing settings or create new
    query = select(Settings).limit(1)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        # Create new settings record
        settings = Settings()
        db.add(settings)

    # Update settings
    settings.aiops_url = settings_data.aiops_url
    settings.api_token = settings_data.api_token
    settings.ssh_host = settings_data.ssh_host
    settings.ssh_port = settings_data.ssh_port
    settings.test_path = settings_data.test_path
    settings.timeout = settings_data.timeout
    settings.parallel_execution = settings_data.parallel_execution
    settings.max_parallel = settings_data.max_parallel
    settings.retry_failed = settings_data.retry_failed
    settings.retry_count = settings_data.retry_count
    settings.updated_by = current_user.username

    await db.commit()
    await db.refresh(settings)

    return {"message": "Settings saved successfully"}


@router.post("/test-connection")
async def test_connection(
    connection_data: ConnectionTestRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test connection to the target AIOps system
    """
    if not connection_data.url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        # Prepare headers
        headers = {}
        if connection_data.token:
            headers["Authorization"] = f"Bearer {connection_data.token}"

        # Test connection with timeout
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{connection_data.url}/health",
                headers=headers,
                follow_redirects=True
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "status_code": response.status_code,
                    "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text[:200]
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed with status {response.status_code}",
                    "status_code": response.status_code
                }

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to the target system. Please check the URL and network connectivity."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Connection timeout. The target system is not responding."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )
