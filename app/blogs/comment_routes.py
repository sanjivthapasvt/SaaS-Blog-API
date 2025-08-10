from typing import List
from fastapi import APIRouter, Depends
from users.models import User
from core.database import get_session, AsyncSession
from sqlmodel import select
from blogs.models import Blog, Comment
from blogs.schema import CommentData
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException
from datetime import timezone, datetime
from blogs.crud import create_comment, read_comments, update_comment, delete_comment

router = APIRouter()


@router.post("/blog/{blog_id}/comment/")
async def create_comment_route(
    blog_id: int,
    content: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    #Post method to create comment in blog needs to be authenticated to perform this action
    try:
        await create_comment(session=session, blog_id=blog_id, content=content, commented_by=current_user.id)         # type: ignore
        return {"detail": "Successfully commented on the blog"}
    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))



@router.get("/blog/{blog_id}/comment/", response_model=List[CommentData])
async def read_comments_route(blog_id:int, session: AsyncSession = Depends(get_session)):
    
    try:
       await read_comments(session=session, blog_id=blog_id)
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


@router.patch("/comment/{comment_id}")
async def update_comment_route(
    comment_id: int,
    content: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        return await update_comment(comment_id=comment_id, content=content, session=session, current_user=current_user.id) # type: ignore
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.delete("/comment/{comment_id}")
async def delete_comment_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        return await update_comment(comment_id=comment_id, content=content, session=session, current_user=current_user.id) # type: ignore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")