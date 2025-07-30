from typing import List
from fastapi import APIRouter, Depends, UploadFile, Form
from users.models import User
from core.database import get_session
from sqlmodel import Session, select
from blogs.models import Blog
from blogs.schema import CommentsData, BlogRead
from blogs.utils import save_thumbnail
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException
import os

router = APIRouter()


@router.post("/create")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    thumbnail: UploadFile | str | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
        Post method for blog to create new blog needs to be authenticated to perform this action.
        Require multipart/formdata input
    """
    try:
        if thumbnail == "": #for edge case if user sends empty string insttead of file
            thumbnail = None

        thumbnail_url = None

        if thumbnail and isinstance(thumbnail, UploadFile):
            thumbnail_url = save_thumbnail(thumbnail)
        
        new_blog = Blog(
            title=title,
            content=content,
            thumbnail_url=thumbnail_url, 
            uploaded_by=current_user.id
            ) 
        
        session.add(new_blog)
        session.commit()
        session.refresh(new_blog)
        title = new_blog.title
        
        return {"title": title, "detail": "Successfully created the blog"}

    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))


@router.patch("/update/{blogs_id}")
async def update_blog_post(
    blog_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    thumbnail: UploadFile | str | None = None ,
    session: Session =  Depends(get_session), 
    current_user:User = Depends(get_current_user)
):
    try:
        blog_post = session.exec(select(Blog).where(Blog.id == blog_id)).first()

        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        if blog_post.uploaded_by != current_user.id:
            raise HTTPException(status_code=401, detail="You are not the owner of the blog")
        
        if thumbnail == "":
            thumbnail = None
            
        thumbnail_url = None

        if thumbnail and isinstance(thumbnail, UploadFile):
            thumbnail_url = save_thumbnail(thumbnail)
        if title:
            blog_post.title = title
        if thumbnail:
            blog_post.thumbnail_url = thumbnail_url
        if content:
            blog_post.content = content
        
        session.add(blog_post)
        session.commit()
        return {"detail": "Successfully updated blog contents"}
        
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")
        
@router.delete("/delete/{blog_id}")
async def delete_blog_post(
    blog_id:int,
    session: Session =  Depends(get_session), 
    current_user:User = Depends(get_current_user)
):
    try:
        blog = session.exec(select(Blog).where(Blog.id == blog_id)).first()

        if not blog:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        if blog.uploaded_by != current_user.id:
            raise HTTPException(status_code=401, detail="You are not the owner of the blog")

        title = blog.title
        
        session.delete(blog)
        session.commit()
        
        return {"title": title, "detail": "Successfully deleted blog"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.get("/all", response_model=List[BlogRead])
async def get_all_blog(session: Session = Depends(get_session)):
    try:
        blogs = session.exec(select(Blog)).all()
        return blogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@router.get("/mine", response_model=List[BlogRead])
async def get_current_user_blog(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        blogs = session.exec(select(Blog).where(Blog.uploaded_by == current_user.id)).all()
        return blogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")