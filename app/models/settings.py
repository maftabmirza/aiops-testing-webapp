"""
System Settings Model
Stores configuration for the target AIOps system and test execution parameters
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Settings(Base):
    """
    System settings for connecting to target AIOps system
    and configuring test execution
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)

    # Target System Configuration
    aiops_url = Column(String(255), nullable=True)
    api_token = Column(String(500), nullable=True)  # Encrypted in production
    ssh_host = Column(String(255), nullable=True)
    ssh_port = Column(Integer, default=22, nullable=True)
    test_path = Column(String(500), nullable=True)
    timeout = Column(Integer, default=30, nullable=False)

    # Test Execution Settings
    parallel_execution = Column(Boolean, default=False, nullable=False)
    max_parallel = Column(Integer, default=5, nullable=False)
    retry_failed = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=3, nullable=False)

    # Metadata
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Settings(aiops_url='{self.aiops_url}')>"
