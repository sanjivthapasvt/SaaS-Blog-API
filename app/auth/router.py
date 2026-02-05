from fastapi import APIRouter

from app.auth.routes import google, local, verification

router = APIRouter()

router.include_router(local.router)
router.include_router(google.router)
router.include_router(verification.router)

