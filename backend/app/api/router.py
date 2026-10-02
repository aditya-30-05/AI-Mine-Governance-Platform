from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.api.mines import router as mines_router
from app.api.inspections import router as inspections_router
from app.api.observations import router as observations_router
from app.api.violations import router as violations_router
from app.api.tasks import router as tasks_router
from app.api.dashboard import router as dashboard_router
from app.api.ai_router import router as ai_router
from app.api.users import router as users_router
from app.api.documents import router as documents_router
from app.api.audit import router as audit_router
from app.api.notifications import router as notifications_router
from app.api.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(mines_router)
api_router.include_router(inspections_router)
api_router.include_router(observations_router)
api_router.include_router(violations_router)
api_router.include_router(tasks_router)
api_router.include_router(dashboard_router)
api_router.include_router(ai_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(audit_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
