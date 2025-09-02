from fastapi import APIRouter

from app.blogs.routes import blogs, bookmarks, comment, likes

router = APIRouter()


router.include_router(blogs.router)
router.include_router(bookmarks.router)
router.include_router(likes.router)
router.include_router(comment.router)
