from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependency import get_current_user
from app.blogs.crud.likes import like_unlike_blog
from app.core.services.database import get_session
from app.users.schema import CurrentUserRead
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Blogs - Likes"])


@router.post(
    "/blogs/{blog_id}/like",
    dependencies=[
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier))
    ],
)
async def like_unlike_blog_route(
    blog_id: int,
    request: Request,
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Toggle like status for a blog post."""
    try:
        return await like_unlike_blog(
            session=session, blog_id=blog_id, current_user=current_user, request=request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while liking post {str(e)}"
        )
