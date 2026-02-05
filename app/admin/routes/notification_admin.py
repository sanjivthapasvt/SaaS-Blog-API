from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.crud.notification_admin import (create_notification,
                                               delete_notification,
                                               get_notification,
                                               list_notifications)
from app.admin.schema import NotificationCreate, NotificationDetail
from app.admin.utils import get_is_admin_user
from app.core.services.database import get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.utils.common_params import get_common_params
from app.utils.logger import logger
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Admin - Notifications"])


@router.get(
    "/notifications",
    response_model=PaginatedResponse[NotificationDetail],
    dependencies=[Depends(get_is_admin_user)],
)
async def list_notifications_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_notifications(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/notifications",
    response_model=NotificationDetail,
    dependencies=[Depends(get_is_admin_user)],
)
async def create_notification_route(
    notification_data: NotificationCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        new_notification = await create_notification(session, notification_data)
        logger.info(f"Admin created notification: {new_notification.id} type: {new_notification.notification_type}")
        return new_notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationDetail,
    dependencies=[Depends(get_is_admin_user)],
)
async def get_notification_route(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_notification(session, notification_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/notifications/{notification_id}",
    dependencies=[Depends(get_is_admin_user)],
)
async def delete_notification_route(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await delete_notification(session, notification_id)
        logger.info(f"Admin deleted notification {notification_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
