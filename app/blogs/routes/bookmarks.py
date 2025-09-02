from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependency import get_current_user
from app.blogs.crud.bookmarks import add_blog_to_bookmark
from app.core.services.database import get_session
from app.users.schema import CurrentUserRead
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Blogs - Bookmarks"])


@router.post(
    "/blogs/{blog_id}/bookmark",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def add_blog_to_bookmark_route(
    blog_id: int,
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Toggle bookmark for a blog post."""
    try:
        return await add_blog_to_bookmark(
            session=session, blog_id=blog_id, user_id=current_user.id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while adding or removing blog from bookmark {str(e)}",
        )
