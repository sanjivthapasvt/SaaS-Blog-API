from fastapi import APIRouter
from app.auth.routes import google, local


router = APIRouter()

router.include_router(local.router)
router.include_router(google.router)