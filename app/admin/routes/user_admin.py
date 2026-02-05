from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.crud.user_admin import (create_user, delete_user,
                                       list_user_detail, list_users,
                                       update_user)
from app.admin.schema import UserCreate, UserDetail, UserUpdate
from app.admin.utils import get_is_admin_user
from app.core.services.database import get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.users.schema import UserRead
from app.utils.common_params import get_common_params
from app.utils.logger import logger
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Admin - User"])


@router.get(
    "/users",
    response_model=PaginatedResponse[UserRead],
    dependencies=[
        Depends(get_is_admin_user),
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


@router.post(
    "/users",
    dependencies=[Depends(RateLimiter(times=15, hours=1)), Depends(get_is_admin_user)],
)
async def create_new_user_route(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create new user by admin
    """
    try:
        user = await create_user(session, user_data)
        logger.info(f"Admin created user: {user.username}")
        return f"Created user {user.username} successfully!"
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )


@router.get(
    "/users/{user_id}",
    dependencies=[Depends(RateLimiter(times=15, hours=1)), Depends(get_is_admin_user)],
    response_model=UserDetail,
)
async def user_detail_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    List user detail by admin
    """
    try:
        user = await list_user_detail(session, user_id)
        return user

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )


@router.patch(
    "/users/{user_id}",
    dependencies=[Depends(RateLimiter(times=15, hours=1)), Depends(get_is_admin_user)],
)
async def update_user_route(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update new user by admin
    """
    try:
        user = await update_user(session, user_id, user_data)
        logger.info(f"Admin updated user {user_id}. Data: {user_data.model_dump(exclude_unset=True)}")
        return f"Updated user {user.username} successfully!"
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(RateLimiter(times=15, hours=1)), Depends(get_is_admin_user)],
)
async def delete_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete user by admin
    """
    try:
        user = await delete_user(session, user_id)
        logger.info(f"Admin deleted user {user_id} ({user})")
        return f"Deleted user {user} successfully!"
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )
