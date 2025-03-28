from fastapi import APIRouter
from . import briefs, payments, content, admin, templates, ab_testing

api_router = APIRouter()
api_router.include_router(briefs.router, prefix="/briefs", tags=["Briefs"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(templates.admin_router, prefix="/admin/templates", tags=["Admin", "Templates"])
api_router.include_router(templates.client_router, prefix="/v1/templates", tags=["Templates"])
api_router.include_router(ab_testing.router, prefix="/ab-testing", tags=["AB Testing"])
