"""Demo users dictionary and mock generator for offline/demo operation."""
import uuid
from app.models import User, UserRole
from app.auth.security import hash_password

DEFAULT_MINE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
DEFAULT_SUB_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

DEMO_USERS_MAP = {
    "admin@coalmine.gov.in": {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "employee_id": "EMP-ADMIN-001",
        "email": "admin@coalmine.gov.in",
        "full_name": "System Administrator",
        "password": "Admin@1234",
        "role": UserRole.ADMIN,
        "department": "IT Administration",
        "mine_id": None,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "admin@coalgov.in": {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "employee_id": "EMP-ADMIN-001",
        "email": "admin@coalgov.in",
        "full_name": "System Administrator",
        "password": "Admin@1234",
        "role": UserRole.ADMIN,
        "department": "IT Administration",
        "mine_id": None,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "manager.a@coalmine.gov.in": {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "employee_id": "EMP-MGR-001",
        "email": "manager.a@coalmine.gov.in",
        "full_name": "Rajesh Kumar Singh",
        "password": "Manager@1234",
        "role": UserRole.MINE_MANAGER,
        "department": "Mine Operations",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "manager.rajrappa@ccl.gov.in": {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "employee_id": "EMP-MGR-001",
        "email": "manager.rajrappa@ccl.gov.in",
        "full_name": "Rajesh Kumar Singh",
        "password": "Manager@1234",
        "role": UserRole.MINE_MANAGER,
        "department": "Mine Operations",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "compliance@coalmine.gov.in": {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "employee_id": "EMP-CO-001",
        "email": "compliance@coalmine.gov.in",
        "full_name": "Priya Sharma",
        "password": "Compliance@1234",
        "role": UserRole.COMPLIANCE_OFFICER,
        "department": "Safety & Compliance",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "inspector.ccl@gov.in": {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "employee_id": "EMP-CO-001",
        "email": "inspector.ccl@gov.in",
        "full_name": "Priya Sharma",
        "password": "Officer@1234",
        "role": UserRole.COMPLIANCE_OFFICER,
        "department": "Safety & Compliance",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "field.officer@coalmine.gov.in": {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "employee_id": "EMP-FO-001",
        "email": "field.officer@coalmine.gov.in",
        "full_name": "Amit Patel",
        "password": "Field@1234",
        "role": UserRole.FIELD_OFFICER,
        "department": "Field Inspection Unit",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "officer@coalmine.gov.in": {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "employee_id": "EMP-FO-001",
        "email": "officer@coalmine.gov.in",
        "full_name": "Amit Patel",
        "password": "Officer@1234",
        "role": UserRole.FIELD_OFFICER,
        "department": "Field Inspection Unit",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "inspector@coalmine.gov.in": {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "employee_id": "EMP-CO-001",
        "email": "inspector@coalmine.gov.in",
        "full_name": "Priya Sharma",
        "password": "Officer@1234",
        "role": UserRole.COMPLIANCE_OFFICER,
        "department": "Safety & Compliance",
        "mine_id": DEFAULT_MINE_ID,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
    "corporate@coalmine.gov.in": {
        "id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
        "employee_id": "EMP-CORP-001",
        "email": "corporate@coalmine.gov.in",
        "full_name": "Sanjay Gupta",
        "password": "Corporate@1234",
        "role": UserRole.CORPORATE_MANAGER,
        "department": "Executive Management",
        "mine_id": None,
        "subsidiary_id": DEFAULT_SUB_ID,
    },
}


def get_demo_user(email: str) -> User | None:
    data = DEMO_USERS_MAP.get(email.strip().lower())
    if not data:
        return None
    return User(
        id=data["id"],
        employee_id=data["employee_id"],
        email=data["email"],
        full_name=data["full_name"],
        hashed_password=hash_password(data["password"]),
        role=data["role"],
        department=data["department"],
        mine_id=data["mine_id"],
        subsidiary_id=data["subsidiary_id"],
        is_active=True,
    )


def get_demo_user_by_id(user_id_str: str) -> User | None:
    try:
        u_uuid = uuid.UUID(user_id_str)
    except Exception:
        return None

    for data in DEMO_USERS_MAP.values():
        if data["id"] == u_uuid:
            return User(
                id=data["id"],
                employee_id=data["employee_id"],
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=hash_password(data["password"]),
                role=data["role"],
                department=data["department"],
                mine_id=data["mine_id"],
                subsidiary_id=data["subsidiary_id"],
                is_active=True,
            )
    # Default fallback
    return User(
        id=u_uuid,
        employee_id="EMP-DEMO-001",
        email="admin@coalmine.gov.in",
        full_name="System Administrator",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
        department="IT Administration",
        mine_id=None,
        subsidiary_id=DEFAULT_SUB_ID,
        is_active=True,
    )
