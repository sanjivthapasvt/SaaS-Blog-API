from typing import List
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from users.models import User
from core.database import get_session
from sqlmodel import Session, func, select
from blogs.models import Blog, Tag, BlogTagLink
from blogs.schema import BlogResponse
from schema.schema import PaginatedResponse
from utils.save_image import save_image
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException

router = APIRouter()

thumbnail_path: str = "blogs/thumbnail"


@router.post("/create")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    tags: str | None = Form(None),
    thumbnail: UploadFile | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
        Post method for blog to create new blog needs to be authenticated to perform this action.
        Require multipart/formdata input
    """
    try:

        thumbnail_url = save_image(thumbnail, thumbnail_path)
        
        new_blog = Blog(
            title=title,
            content=content,
            thumbnail_url=thumbnail_url, 
            author=current_user.id
        ) 
        
        session.add(new_blog)
        session.commit()
        session.refresh(new_blog)
        title = new_blog.title

        if tags:
            tag_list = [t.strip() for t in tags.split("#") if t.strip()]
            for tag in tag_list:
                current_tag = session.exec(select(Tag).where(Tag.title == tag)).first()
                if not current_tag:
                    current_tag = Tag(title=tag)
                    session.add(current_tag)
                    session.commit()
                    session.refresh(current_tag)
                new_link = BlogTagLink(blog_id=new_blog.id, tag_id=current_tag.id)
                session.add(new_link)
                session.commit()

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
    thumbnail: UploadFile | None = None ,
    session: Session =  Depends(get_session), 
    current_user:User = Depends(get_current_user)
):
    try:
        blog_post = session.exec(select(Blog).where(Blog.id == blog_id)).first()

        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        if blog_post.author != current_user.id:
            raise HTTPException(status_code=401, detail="You are not the owner of the blog")
        
        thumbnail_url = save_image(thumbnail, thumbnail_path)
        
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
        
        if blog.author != current_user.id:
            raise HTTPException(status_code=401, detail="You are not the owner of the blog")

        title = blog.title
        
        session.delete(blog)
        session.commit()
        
        return {"title": title, "detail": "Successfully deleted blog"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.get("/all", response_model=PaginatedResponse[BlogResponse])
async def get_all_blog(
    search: str = Query(default=None),
    limit :int = Query(10, ge=1),
    offset: int = Query(0, ge=0), 
    session: Session = Depends(get_session)
):
    try:
        query = select(Blog).offset(offset).limit(limit)
        total_query = select(func.count()).select_from(Blog)
        
        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(Blog.title).like(search_term)
            query = query.where(condition)
            total_query = total_query.where(condition)

        blogs = session.exec(query).all()

        total = session.exec(total_query).one()
        
        result = [{
            "id": blog.id,
            "title": blog.title,
            "content": blog.content,
            "thumbnail_url": blog.thumbnail_url,
            "author": blog.author,
            "created_at": blog.created_at,
            "tags": [tag.title for tag in blog.tags]
        }for blog in blogs]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": result,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@router.get("/mine", response_model = PaginatedResponse[BlogResponse])
async def get_current_user_blog(
    search: str = Query(default=None),
    limit:int = Query(10, ge=1),
    offset:int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        query = select(Blog).offset(offset).limit(limit).where(Blog.author == current_user.id)
        total_query = select(func.count()).select_from(Blog).where(Blog.author == current_user.id)
        
        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(Blog.title).like(search_term)

            query = query.where(condition)
            total_query = total_query.where(condition)

        blogs = session.exec(query).all()

        total = session.exec(total_query).one()
                        
        result = [{
            "id": blog.id,
            "title": blog.title,
            "content": blog.content,
            "thumbnail_url": blog.thumbnail_url,
            "author": blog.author,
            "created_at": blog.created_at,
            "tags": [tag.title for tag in blog.tags]
        }for blog in blogs]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": result,
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")