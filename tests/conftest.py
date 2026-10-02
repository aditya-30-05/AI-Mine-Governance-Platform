"""Pytest test configuration and fixtures."""
import sys
import os
from pathlib import Path
import pytest
import asyncio
from datetime import datetime, timedelta
import uuid

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEMO_MODE"] = "True"
os.environ["SECRET_KEY"] = "test_super_secret_jwt_key_12345"

from app.config import settings
from app.auth.security import hash_password, create_access_token
from app.models import User, UserRole


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_admin_user():
    return User(
        id=uuid.uuid4(),
        email="admin@coalgov.in",
        full_name="National DGMS Admin",
        role=UserRole.ADMIN,
        designation="Chief Inspector of Mines",
        phone="+91-9876543210",
        is_active=True,
    )


@pytest.fixture
def mock_safety_officer():
    return User(
        id=uuid.uuid4(),
        email="safety@mine-a.coalgov.in",
        full_name="Rajesh Kumar Verma",
        role=UserRole.COMPLIANCE_OFFICER,
        designation="Senior Safety Officer",
        phone="+91-9876543211",
        is_active=True,
    )


@pytest.fixture
def valid_jwt_token(mock_admin_user):
    return create_access_token({"sub": str(mock_admin_user.id), "role": mock_admin_user.role.value})
