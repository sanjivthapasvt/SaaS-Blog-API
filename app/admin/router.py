from fastapi import APIRouter

from app.admin.routes import user_admin, blog_admin, notification_admin

router = APIRouter()

router.include_router(user_admin.router)
router.include_router(blog_admin.router)
router.include_router(notification_admin.router)
