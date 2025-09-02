from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi_limiter.depends import RateLimiter

from app.auth.dependency import get_current_user
from app.core.services.database import AsyncSession, get_session
from app.users.crud.follow import follow_user, unfollow_user
from app.users.models import User
from app.users.schema import CurrentUserRead
from app.utils.rate_limiter import user_identifier

router = APIRouter(tags=["Users - Follow"])


@router.post(
    "/users/{user_id}/follow",
    dependencies=[
        Depends(RateLimiter(times=25, minutes=1, identifier=user_identifier))
    ],
)
async def follow_user_route(
    user_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    try:
        target_user = await follow_user(
            session=session, user_id=user_id, current_user=current_user, request=request
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
