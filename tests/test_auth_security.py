"""Unit tests for authentication and RBAC security."""
import pytest
import uuid
from datetime import datetime, timedelta
from jose import jwt
from app.auth.security import hash_password, verify_password, create_access_token
from app.config import settings
from app.models import UserRole


def test_password_hashing():
    """Verify that bcrypt hashes correctly and verifies plain passwords."""
    plain = "MineAdmin@2026!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_token_creation_and_payload():
    """Verify JWT access token contains correct sub, role, and expiration."""
    user_id = str(uuid.uuid4())
    token = create_access_token(
        data={"sub": user_id, "role": UserRole.MINE_MANAGER.value},
        expires_delta=timedelta(minutes=30),
    )

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["role"] == UserRole.MINE_MANAGER.value
    assert "exp" in payload


def test_user_roles_coverage():
    """Verify all defined coal governance roles exist."""
    expected_roles = [
        "admin",
        "field_officer",
        "compliance_officer",
        "mine_manager",
        "corporate_manager",
    ]
    actual_roles = [r.value for r in UserRole]
    for r in expected_roles:
        assert r in actual_roles

