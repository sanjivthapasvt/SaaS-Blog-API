from typing import List
from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from sqlalchemy import func
from users.models import User, UserFollowLink
from core.database import Session, get_session
from auth.auth import get_current_user
from sqlmodel import select
from users.schema import CurrentUserRead, UserRead
from auth.utils import hash_password, verify_password
from models.schema import PaginatedResponse
from utils.save_image import save_image


router = APIRouter()

profile_pic_path: str = "users/profile_pic"

@router.post("/user/{user_id}/follow")
async def follow_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    try:
        target_user = session.get(User, user_id)

        if not target_user:
            raise HTTPException(status_code=404, detail="User doesn't exist")
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

        return {"message": f"You are now following {target_user.full_name}"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.delete("/user/{user_id}/follow")
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

        return {"message": f"You have succesfully unfollowed {target_user.full_name}"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


###############################################
##List User, Followers and Following routes####
###############################################

@router.get("/user", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_all_users(
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    try:
        query = select(User).limit(limit).offset(offset)
        total_query = select(func.count()).select_from(User)

        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(User.full_name).like(search_term)
            query = query.where(condition)
        
        total = session.exec(total_query).one()
        users = session.exec(query).all()
 
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": users
        }
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")



@router.get("/user/{user_id}/followers", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_followers(
    user_id: int,
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)
):
    try:
        raw_followers = session.exec(
            select(UserFollowLink.follower_id).limit(limit).offset(offset).where(UserFollowLink.following_id == user_id)
        ).all()
        
        query = select(User).where(User.id.in_(raw_followers)) # type: ignore

        total_query = select(func.count()).select_from(UserFollowLink).where(UserFollowLink.following_id == user_id)
        
        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(User.full_name).like(search_term)
            query = query.where(condition)
        
        
        total = session.exec(total_query).one()
        followers = session.exec(query).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": followers
        }
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while listing followers {str(e)}")



@router.get("/user/{user_id}/following", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_followings(
    user_id: int,
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    try:  
        raw_followings = session.exec(
            select(UserFollowLink.following_id).limit(limit).offset(offset).where(UserFollowLink.follower_id == user_id)
            ).all()
        
        query = select(User).where(User.id.in_(raw_followings)) # type: ignore
        total_query = select(func.count()).select_from(UserFollowLink).where(UserFollowLink.follower_id == user_id)
        
        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(User.full_name).like(search_term)
            query = query.where(condition)
        
        
        total = session.exec(total_query).one()
        followings = session.exec(query).all()
            
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": followings
        }
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")
    

#########################
###Current User Action###
#########################

@router.get("/user/me", response_model=CurrentUserRead)
async def get_current_user_info(
    session: Session = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    try:
        query = select(User).where(User.id == current_user.id)

        user_data = session.exec(query).first()
 
        return user_data
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.post("/user/me/password")
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



@router.patch("/user/me")
def update_user_profile(
    full_name: str | None = Form(None),
    profile_pic: UploadFile | None =  None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        if not full_name or not profile_pic:
            raise HTTPException(status_code=400, detail="Both fields cannot be empty. At least one field must be provided")
        
        if full_name:
            current_user.full_name = full_name
        
        if profile_pic:
            profile_pic_url = save_image(profile_pic, profile_pic_path)
            current_user.profile_pic = profile_pic_url

        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        return {"detail": "Successfully updated user profile"}

    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while updating user profile {str(e)}")