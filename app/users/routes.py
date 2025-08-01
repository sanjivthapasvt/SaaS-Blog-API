from typing import List
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from users.models import User, UserFollowLink
from core.database import Session, get_session
from auth.auth import get_current_user
from sqlmodel import select
from users.schema import UserRead
from auth.utils import hash_password, verify_password


router = APIRouter()


@router.post("/follow/{user_id}")
async def follow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    try:
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
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.delete("/unfollow/{user_id}")
async def unfollow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    try:
        target_user = session.get(User, user_id)

        if not target_user:
            raise HTTPException(status_code=404, detail="User doesnot exist")
        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        #Check if the user is following
        link = session.exec(select(UserFollowLink).where(
            UserFollowLink.follower_id == current_user.id,
            UserFollowLink.following_id == target_user.id
        )).first()

        if not link:
            raise HTTPException(status_code=400, detail="You have not followed the user")

        session.delete(link)
        session.commit()

        return {"message": f"You have succesfully unfollowed {target_user.username}"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.patch("/changepassword")
def change_password(
    current_password: str,
    new_password: str,
    again_new_password: str,
    session: Session =  Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.hashed_password:
            if not verify_password(current_password, current_user.hashed_password):
                raise HTTPException(status_code=400, detail="Your old password doesn't match")

        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Password length must be greater than 6")

        if new_password != again_new_password:
            raise HTTPException(status_code=400, detail="New passwords doesn't match")
        
        hashed_new_password = hash_password(new_password)

        current_user.hashed_password = hashed_new_password
        session.add(current_user)
        session.commit()
        return {"detail": "Successfully changed password"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")

@router.get("/list", response_model=List[UserRead])
async def list_all_users(
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    try:
        users = session.exec(select(User.id, User.full_name).where(User.id != current_user.id)).all()
 
        return users
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")



@router.get("/list/followers", response_model=List[UserRead])
async def list_followers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        raw_followers = session.exec(
            select(UserFollowLink.follower_id).where(UserFollowLink.following_id == current_user.id)
        ).all()

        followers = session.exec(
            select(User).where(User.id.in_(raw_followers)) # type: ignore
        ).all()
        
        return followers
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while listing followers {str(e)}")



@router.get("/list/followings", response_model=List[UserRead])
async def list_followings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    raw_followings = []
    followings = []
    try:  
        raw_followings = session.exec(
            select(UserFollowLink.following_id).where(UserFollowLink.follower_id == current_user.id)
            ).all()
        
        if raw_followings:
            followings = session.exec(
                select(User).where(User.id.in_(raw_followings)) # type: ignore
                ).all()
            
        return followings
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")