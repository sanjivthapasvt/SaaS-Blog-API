from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.auth.hashing import hash_password, verify_password
from app.auth.security import check_password_strength
from app.notifications.models import Notification
from app.notifications.notification_service import (NotificationType,
                                                    create_notification)
from app.users.models import User, UserFollowLink
from app.users.schema import CurrentUserRead
from app.utils.remove_image import remove_image
from app.utils.save_image import save_image

profile_pic_path: str = "users/profile_pic"


async def get_user_info(session: AsyncSession, user_id: int):
    query = select(User).where(User.id == user_id)
    user_data = await session.execute(query)
    user_data_result = user_data.scalars().first()

    return user_data_result


async def change_user_password(
    session: AsyncSession,
    current_user: User,
    current_password: str,
    new_password: str,
    again_new_password: str,
):
    if current_user.hashed_password:
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Your old password doesn't match"
            )


    strong, reasons = check_password_strength(new_password)
    if not strong:
        raise HTTPException(status_code=400, detail={"password": new_password, "reasons": reasons}) 

    if new_password != again_new_password:
        raise HTTPException(status_code=400, detail="New passwords doesn't match")

    hashed_new_password = hash_password(new_password)

    current_user.hashed_password = hashed_new_password
    session.add(current_user)
    await session.commit()


async def update_user_profile(
    full_name: str | None,
    profile_pic: UploadFile | None,
    session: AsyncSession,
    current_user: User,
):
    if not full_name and not profile_pic:
        raise HTTPException(
            status_code=400,
            detail="Both fields cannot be empty. At least one field must be provided",
        )

    if full_name is not None and full_name.strip() != "":
        current_user.full_name = full_name

    if profile_pic:
        if current_user.profile_pic:
            await remove_image(current_user.profile_pic)
        profile_pic_url = await save_image(profile_pic, profile_pic_path)
        current_user.profile_pic = profile_pic_url

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)


async def list_users(search: str | None, limit: int, offset: int, session: AsyncSession):
    query = select(User)
    total_query = select(func.count()).select_from(User)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        query = query.where(condition)

    total = await session.execute(total_query.limit(limit).offset(offset))
    total_result = total.scalars().one()
    users = await session.execute(query)
    users_result = users.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": users_result,
    }


async def list_followers(
    user_id: int, search: str | None, limit: int, offset: int, session: AsyncSession
):
    raw_followers = await session.execute(
        select(UserFollowLink.follower_id)
        .where(UserFollowLink.following_id == user_id)
        .limit(limit)
        .offset(offset)
    )
    raw_followers_result = raw_followers.scalars().all()
    query = select(User).where(User.id.in_(raw_followers_result))  # type: ignore

    total_query = (
        select(func.count())
        .select_from(UserFollowLink)
        .where(UserFollowLink.following_id == user_id)
    )

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        query = query.where(condition)

    total = await session.execute(total_query)
    total_result = total.scalars().one()
    followers = await session.execute(query)
    followers_result = followers.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": followers_result,
    }


async def list_followings(
    user_id: int, search: str | None, limit: int, offset: int, session: AsyncSession
):
    raw_followings = await session.execute(
        select(UserFollowLink.following_id)
        .where(UserFollowLink.follower_id == user_id)
        .limit(limit)
        .offset(offset)
    )
    raw_followings_result = raw_followings.scalars().all()
    query = select(User).where(User.id.in_(raw_followings_result))  # type: ignore
    total_query = (
        select(func.count())
        .select_from(UserFollowLink)
        .where(UserFollowLink.follower_id == user_id)
    )

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        query = query.where(condition)

    total = await session.execute(total_query)
    total_result = total.scalars().one()
    followings = await session.execute(query)
    followings_result = followings.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": followings_result,
    }


async def follow_user(
    user_id: int, session: AsyncSession, current_user: CurrentUserRead
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
