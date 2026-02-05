from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter

from app.auth.dependency import get_current_user
from app.auth.schemas import UserRead
from app.blogs.crud.comments import (
    create_comment,
    delete_comment,
    get_comment_replies,
    read_comments,
    update_comment,
)
from app.blogs.schema import CommentResponse, CommentWrite
from app.core.services.database import AsyncSession, get_session
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Comments"])


@router.post(
    "/blogs/{blog_id}/comments",
    dependencies=[
        Depends(RateLimiter(times=15, minutes=1, identifier=user_identifier))
    ],
)
async def create_comment_route(
    blog_id: int,
    comment_data: CommentWrite,
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    # Post method to create comment in blog needs to be authenticated to perform this action
    try:
        await create_comment(
            session=session,
            blog_id=blog_id,
            content=comment_data.content,
            commented_by=current_user.id,
            parent_id=comment_data.parent_id,
        )
        return {"detail": "Successfully commented on the blog"}

    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))


@router.get(
    "/blogs/{blog_id}/comments",
    response_model=list[CommentResponse],
    dependencies=[
        Depends(RateLimiter(times=30, minutes=1, identifier=user_identifier))
    ],
)
async def read_comments_route(
    blog_id: int, session: AsyncSession = Depends(get_session)
):

    try:
        return await read_comments(session=session, blog_id=blog_id)
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


@router.patch(
    "/comments/{comment_id}",
    dependencies=[Depends(RateLimiter(times=20, hours=1, identifier=user_identifier))],
)
async def update_comment_route(
    comment_id: int,
    comment_data: CommentWrite,
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        return await update_comment(
            comment_id=comment_id,
            content=comment_data.content,
            session=session,
            current_user=current_user.id,
        )
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.delete(
    "/comments/{comment_id}",
    dependencies=[Depends(RateLimiter(times=30, hours=1, identifier=user_identifier))],
)
async def delete_comment_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        return await delete_comment(
            comment_id=comment_id, session=session, current_user=current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.post(
    "/blogs/{blog_id}/comments/{comment_id}/reply",
    dependencies=[
        Depends(RateLimiter(times=15, minutes=1, identifier=user_identifier))
    ],
)
async def reply_to_comment_route(
    blog_id: int,
    comment_id: int,
    comment_data: CommentWrite,
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """
    Reply to an existing comment.
    """
    try:
        await create_comment(
            session=session,
            blog_id=blog_id,
            content=comment_data.content,
            commented_by=current_user.id,
            parent_id=comment_id,
        )
        return {"detail": "Successfully replied to the comment"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


@router.get(
    "/comments/{comment_id}/replies",
    response_model=list[CommentResponse],
    dependencies=[
        Depends(RateLimiter(times=30, minutes=1, identifier=user_identifier))
    ],
)
async def get_replies_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all replies to a specific comment.
    """
    try:
        return await get_comment_replies(comment_id=comment_id, session=session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")
