from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.notifications.models import Notification
from app.notifications.service import NotificationType, create_notification
from app.users.models import User, UserFollowLink
from app.users.schema import CurrentUserRead


async def follow_user(
    user_id: int,
    session: AsyncSession,
    current_user: CurrentUserRead,
    request: Request | None = None,
) -> User:
    target_user = await session.get(User, user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User doesn't exist")

    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Check if the user is already following
    link = await session.execute(
        select(UserFollowLink).where(
            UserFollowLink.follower_id == current_user.id,
            UserFollowLink.following_id == target_user.id,
        )
    )

    link_result = link.scalar_one_or_none()
    if link_result:
        raise HTTPException(status_code=400, detail="Already following")

    notification_result = await session.execute(
        select(Notification).where(
            (Notification.owner_id == target_user.id)
            & (Notification.blog_id == None)
            & (Notification.notification_type == NotificationType.FOLLOW)
            & (Notification.triggered_by_user_id == current_user.id)
        )
    )

    if not notification_result.scalars().first():
        await create_notification(
            session=session,
            owner_id=target_user.id,  # type: ignore
            triggered_by_user_id=current_user.id,
            message=f"{current_user.full_name} started following you",
            notification_type=NotificationType.FOLLOW,
            blog_id=None,
            request=request,
        )

    newlink = UserFollowLink(follower_id=current_user.id, following_id=target_user.id)

    session.add(newlink)
    await session.commit()
    return target_user


async def unfollow_user(user_id: int, session: AsyncSession, current_user: User):
    target_user = await session.get(User, user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User does not exist")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")

    # Check if the user is following
    link = await session.execute(
        select(UserFollowLink).where(
            UserFollowLink.follower_id == current_user.id,
            UserFollowLink.following_id == target_user.id,
        )
    )

    link_result = link.scalar_one_or_none()

    if not link_result:
        raise HTTPException(status_code=400, detail="You have not followed the user")

    await session.delete(link_result)
    await session.commit()
    return target_user.full_name
