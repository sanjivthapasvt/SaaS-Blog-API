from typing import List
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from app.users.models import User
from app.core.database import get_session, AsyncSession
from app.blogs.schema import CommentData, CommentWrite
from app.auth.auth import get_current_user
from app.blogs.crud import create_comment, read_comments, update_comment, delete_comment

router = APIRouter()


@router.post("/blogs/{blog_id}/comments")
async def create_comment_route(
    blog_id: int,
    comment_data: CommentWrite,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    #Post method to create comment in blog needs to be authenticated to perform this action
    try:
        await create_comment(session=session, blog_id=blog_id, content=comment_data.content, commented_by=current_user.id)         # type: ignore
        return {"detail": "Successfully commented on the blog"}
    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))



@router.get("/blogs/{blog_id}/comments")
async def read_comments_route(blog_id:int, session: AsyncSession = Depends(get_session)):
    
    try:
       return await read_comments(session=session, blog_id=blog_id)
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong {str(e)}")


@router.patch("/comments/{comment_id}")
async def update_comment_route(
    comment_id: int,
    comment_data: CommentWrite,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        return await update_comment(comment_id=comment_id, content=comment_data.content, session=session, current_user=current_user.id) # type: ignore
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.delete("/comments/{comment_id}")
async def delete_comment_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        return await delete_comment(comment_id=comment_id, session=session, current_user=current_user.id) # type: ignore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")