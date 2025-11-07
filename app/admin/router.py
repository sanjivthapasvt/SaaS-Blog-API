from fastapi import APIRouter

from app.admin.routes import user_admin

router = APIRouter()

router.include_router(user_admin.router)
