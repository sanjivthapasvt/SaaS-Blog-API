from typing import List
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from users.models import User, UserFollowLink
from core.database import Session, get_session
from auth.auth import get_current_user
from sqlmodel import select
from users.schema import UserRead
router = APIRouter()

@router.post("/follow/{user_id}")
async def follow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    target_user = session.get(User, user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User doesnot exist")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    #Check if the user is already following
    link = session.exec(select(UserFollowLink).where(
        UserFollowLink.follower_id == current_user.id,
        UserFollowLink.following_id == target_user.id
    )).first()

    if link:
        raise HTTPException(status_code=400, detail="Already following")
    
    newlink = UserFollowLink(follower_id=current_user.id, following_id=target_user.id)

    session.add(newlink)
    session.commit()

    return {"message": f"You are now following {target_user.username}"}


@router.get("/list", response_model=List[UserRead])
async def list_all_users(
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    users = session.exec(select(User.id, User.full_name).where(User.id != current_user.id)).all()
 
    return users