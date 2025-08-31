from fastapi import APIRouter

from app.users.routes import follow, me, users

router = APIRouter()

router.include_router(follow.router)
router.include_router(me.router)
router.include_router(users.router)
