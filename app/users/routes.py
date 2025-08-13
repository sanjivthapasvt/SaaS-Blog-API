from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from app.blogs.crud import get_user_blogs
from app.users.models import User
from app.core.database import AsyncSession, get_session
from app.auth.auth import get_current_user
from app.users.schema import CurrentUserRead, UserRead
from app.models.schema import PaginatedResponse
from app.users.crud import(
    list_users, 
    list_followers, 
    list_followings, 
    get_user_info, 
    change_user_password, 
    update_user_profile, 
    follow_user, 
    unfollow_user
)

router = APIRouter()

#########################
###Current User Action###
#########################

@router.get("/users/me", response_model=CurrentUserRead)
async def get_current_user_info_route(
    session: AsyncSession = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    try:
        return get_user_info(session=session, user_id=current_user.id) # type: ignore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.patch("/users/me")
async def update_user_profile_route(
    full_name: str | None = Form(None),
    profile_pic: UploadFile | None =  None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        await update_user_profile(session=session, profile_pic=profile_pic, full_name=full_name, current_user=current_user)
        return {"detail": "Successfully updated user profile"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while updating user profile {str(e)}")
    

@router.post("/users/me/password")
async def change_password_route(
    current_password: str,
    new_password: str,
    again_new_password: str,
    session: AsyncSession =  Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        await change_user_password(session=session, current_user=current_user, current_password=current_password, new_password=new_password, again_new_password=again_new_password)
        return {"detail": "Successfully changed password"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")



################################################
###List User, Followers and Following routes####
################################################

@router.get("/users", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_users_route(
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_users(session=session, search=search, limit=limit, offset=offset) 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")



@router.get("/users/{user_id}/followers", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_followers_route(
    user_id: int,
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    try:
        return await list_followers(session=session, user_id=user_id, search=search, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while listing followers {str(e)}")



@router.get("/users/{user_id}/following", response_model=PaginatedResponse[UserRead], dependencies=[Depends(get_current_user)])
async def list_followings_route(
    user_id: int,
    search: str = Query(default=None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    try:  
        return await list_followings(session=session, user_id=user_id, search=search, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")
    

##########################
###Follow Unfollow User###
##########################
@router.post("/users/{user_id}/follow")
async def follow_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    try:
        target_user = await follow_user(session=session, user_id=user_id, current_user=current_user)
        return {"message": f"You are now following {target_user.full_name}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.delete("/users/{user_id}/follow")
async def unfollow_user_route(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user:User = Depends(get_current_user),
):
    try:
        target_user = await unfollow_user(session=session, user_id=user_id, current_user=current_user)
        return {"message": f"You have succesfully unfollowed {target_user.full_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

#####################
###List User Blogs###
#####################

@router.get("/users/{user_id}/blogs")
async def list_user_blog_route(
    user_id: int,
    search: str | None = Query(default=None),
    limit:int = Query(10, ge=1),
    offset:int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    try:
        return get_user_blogs(session=session, search=search, limit=limit, offset=offset, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")