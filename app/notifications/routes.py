from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependency import get_current_user
from app.auth.schemas import UserRead
from app.core.database import get_session
from app.models.schema import PaginatedResponse
from app.notifications.crud import get_notifications, mark_notification_as_read
from app.notifications.schema import NotificationResponse
from app.utils.rate_limiter import user_identifier

router = APIRouter()


@router.get(
    "/notifications",
    response_model=PaginatedResponse[NotificationResponse],
    dependencies=[
        Depends(RateLimiter(times=15, minutes=1, identifier=user_identifier))
    ],
)
async def get_notifications_route(
    search: str | None = Query(default=None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        notifications_result, total_result = await get_notifications(
            session=session,
            search=search,
            limit=limit,
            offset=offset,
            current_user=current_user.id,
        )

        return PaginatedResponse[NotificationResponse](
            total=total_result,
            limit=limit,
            offset=offset,
            data=[
                NotificationResponse.model_validate(obj) for obj in notifications_result
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while getting notification {str(e)}",
        )


@router.post(
    "/notifications/{notification_id}/mark_as_read",
    dependencies=[Depends(RateLimiter(times=5, minutes=1, identifier=user_identifier))],
)
async def mark_as_read_route(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    try:
        return await mark_notification_as_read(
            session=session,
            notification_id=notification_id,
            current_user=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while marking notification as read {str(e)}",
        )
