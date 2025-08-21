from typing import List
from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter

from app.auth.dependency import get_current_user
from app.blogs.crud import get_user_blogs
from app.blogs.schema import BlogResponse
from app.core.database import AsyncSession, get_session
from app.models.schema import PaginatedResponse, CommonParams
from app.users.crud import (change_user_password, follow_user, get_user_info,
                            list_followers, list_followings, list_users,
                            unfollow_user, update_user_profile)
from app.users.models import User
from app.users.schema import CurrentUserRead, UserChangePassword, UserRead, UserResponse
from app.utils.rate_limiter import user_identifier
from app.utils.common_params import get_common_params


router = APIRouter()

#########################
###Current User Action###
#########################


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
        return await get_user_info(session=session, user_id=current_user.id)
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
        blogs_result, total_result = await get_user_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            user_id=current_user.id,
            tags=tags
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


################################################
###List User, Followers and Following routes####
################################################


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
            session=session, search=params.search, limit=params.limit, offset=params.offset
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
            session=session, user_id=user_id, search=params.search, limit=params.limit, offset=params.offset
        )
        data = [
            UserResponse.model_validate(
                user
            )for user in followers
        ]
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
        followings, total =  await list_followings(
            session=session, user_id=user_id, search=params.search, limit=params.limit, offset=params.offset
        )
        
        data = [
            UserResponse.model_validate(user)
            for user in followings
        ]
        return PaginatedResponse[UserResponse](
            total=total, limit=params.limit, offset=params.offset, data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


##########################
###Follow Unfollow User###
##########################
@router.post(
    "/users/{user_id}/follow",
    dependencies=[
        Depends(RateLimiter(times=25, minutes=1, identifier=user_identifier))
    ],
)
async def follow_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    try:
        target_user = await follow_user(
            session=session, user_id=user_id, current_user=current_user
        )
        return {"message": f"You are now following {target_user.full_name}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.delete(
    "/users/{user_id}/follow",
    dependencies=[
        Depends(RateLimiter(times=25, minutes=1, identifier=user_identifier))
    ],
)
async def unfollow_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        target_user = await unfollow_user(
            session=session, user_id=user_id, current_user=current_user
        )
        return {"message": f"You have succesfully unfollowed {target_user}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


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
        blogs_result, total_result = await get_user_blogs(
            session=session, search=params.search, limit=params.limit, offset=params.offset, user_id=user_id, tags=tags
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
