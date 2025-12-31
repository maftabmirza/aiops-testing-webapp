#!/usr/bin/env python3
"""
Script to create default admin user
Usage: python scripts/create_admin.py
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.user import User
from app.auth import get_password_hash
from app.config import settings


async def create_admin_user():
    """
    Create default admin user if it doesn't exist
    """
    # Create async engine
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
        echo=False
    )

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if admin user already exists
        query = select(User).where(User.username == "admin")
        result = await session.execute(query)
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin user already exists!")
            print(f"  Username: {existing_admin.username}")
            print(f"  Email: {existing_admin.email}")
            print(f"  Is Admin: {existing_admin.is_admin}")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@aiops.local",
            hashed_password=get_password_hash("admin"),
            is_admin=True,
            is_active=True
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print("Admin user created successfully!")
        print(f"  Username: admin")
        print(f"  Password: admin")
        print(f"  Email: admin@aiops.local")
        print(f"  ID: {admin_user.id}")
        print("\nPlease change the password after first login!")

    await engine.dispose()


if __name__ == "__main__":
    print("Creating default admin user...")
    asyncio.run(create_admin_user())
