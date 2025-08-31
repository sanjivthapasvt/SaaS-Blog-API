from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter

from app.auth.dependency import get_current_user
from app.blogs.crud.blogs import list_user_blogs
from app.blogs.schema import BlogResponse
from app.core.database import AsyncSession, get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.users.crud.users import list_followers, list_followings, list_users
from app.users.schema import UserRead, UserResponse
from app.utils.common_params import get_common_params
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Users - List"])


@router.get(
    "/users",
    response_model=PaginatedResponse[UserRead],
    dependencies=[
        Depends(get_current_user),
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier)),
    ],
)
async def list_users_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_users(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.get(
    "/users/{user_id}/followers",
    response_model=PaginatedResponse[UserRead],
    dependencies=[
        Depends(get_current_user),
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier)),
    ],
)
async def list_followers_route(
    user_id: int,
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:

        followers, total = await list_followers(
            session=session,
            user_id=user_id,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
        data = [UserResponse.model_validate(user) for user in followers]
        return PaginatedResponse[UserResponse](
            total=total, limit=params.limit, offset=params.offset, data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while listing followers {str(e)}",
        )


@router.get(
    "/users/{user_id}/following",
    response_model=PaginatedResponse[UserRead],
    dependencies=[
        Depends(get_current_user),
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier)),
    ],
)
async def list_followings_route(
    user_id: int,
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        followings, total = await list_followings(
            session=session,
            user_id=user_id,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )

        data = [UserResponse.model_validate(user) for user in followings]
        return PaginatedResponse[UserResponse](
            total=total, limit=params.limit, offset=params.offset, data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


#####################
###List User Blogs###
#####################


@router.get(
    "/users/{user_id}/blogs",
    dependencies=[
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier))
    ],
)
async def list_user_blog_route(
    user_id: int,
    tags: List[str] | None = Query(None),
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        blogs_result, total_result = await list_user_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            user_id=user_id,
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
