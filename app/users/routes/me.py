from typing import List

from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter

from app.auth.dependency import get_current_user
from app.blogs.crud.blogs import list_user_blogs
from app.blogs.schema import BlogResponse
from app.core.services.database import AsyncSession, get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.users.crud.me import change_user_password, update_user_profile
from app.users.crud.users import list_user_bookmarks, list_user_info
from app.users.models import User
from app.users.schema import CurrentUserRead, UserChangePassword, UserRead
from app.utils.common_params import get_common_params
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Users - Me"])

from typing import List

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.blogs.crud.likes import get_liked_blogs


@router.get(
    "/users/me",
    response_model=CurrentUserRead,
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def get_current_user_info_route(
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        return await list_user_info(session=session, user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.patch(
    "/users/me",
    dependencies=[Depends(RateLimiter(times=5, minutes=1, identifier=user_identifier))],
)
async def update_user_profile_route(
    full_name: str | None = Form(None),
    profile_pic: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await update_user_profile(
            session=session,
            profile_pic=profile_pic,
            full_name=full_name,
            current_user=current_user,
        )
        return {"detail": "Successfully updated user profile"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while updating user profile {str(e)}",
        )


@router.post(
    "/users/me/password",
    dependencies=[Depends(RateLimiter(times=5, hours=1, identifier=user_identifier))],
)
async def change_password_route(
    password_info: UserChangePassword,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        await change_user_password(
            session=session,
            current_user=current_user,
            current_password=password_info.current_password,
            new_password=password_info.new_password,
            again_new_password=password_info.again_new_password,
        )
        return {"detail": "Successfully changed password"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


@router.get(
    "/users/me/blogs",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def list_current_user_blog_route(
    params: CommonParams = Depends(get_common_params),
    tags: List[str] | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        blogs_result, total_result = await list_user_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            user_id=current_user.id,
            tags=tags,
        )

        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return PaginatedResponse[BlogResponse](
            total=total_result, limit=params.limit, offset=params.offset, data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.get(
    "/users/me/blogs/bookmarks",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def list_bookmarks_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        blogs, total = await list_user_bookmarks(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            user_id=current_user.id,
        )

        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs
        ]

        return PaginatedResponse[BlogResponse](
            total=total, limit=params.limit, offset=params.offset, data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while listing bookmark {str(e)}",
        )


@router.get(
    "/users/me/blogs/liked",
    response_model=PaginatedResponse[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=30, minutes=1, identifier=user_identifier))
    ],
)
async def get_liked_blog_route(
    params: CommonParams = Depends(get_common_params),
    current_user: CurrentUserRead = Depends(get_current_user),
    tags: List[str] | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve blogs liked by the current user."""
    try:
        blogs_result, total_result = await get_liked_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            user_id=current_user.id,
            tags=tags,
        )

        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return PaginatedResponse[BlogResponse](
            total=total_result, limit=params.limit, offset=params.offset, data=data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
