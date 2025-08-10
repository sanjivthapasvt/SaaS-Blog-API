from fastapi import APIRouter, Depends, Query, UploadFile, Form
from users.schema import CurrentUserRead
from core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from blogs.schema import BlogContentResponse, BlogResponse
from models.schema import PaginatedResponse
from utils.save_image import save_image
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException
from blogs.crud import (
    get_blog_by_id, 
    create_new_blog, 
    like_unlike_blog, 
    get_all_blogs, 
    get_liked_blogs, 
    get_current_user_blog, 
    update_blog, 
    delete_blog
)


router = APIRouter()

thumbnail_path: str = "blogs/thumbnail"


@router.post("/blog")
async def create_blog_route(
    title: str = Form(...),
    content: str = Form(...),
    tags: str | None = Form(None),
    thumbnail: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user)
):
    try:

        thumbnail_url = await save_image(thumbnail, thumbnail_path)
        new_blog = await create_new_blog(
            session=session, 
            title=title, 
            thumbnail_url=thumbnail_url, 
            content=content, 
            author=current_user.id,
            tags=tags
        )

        title = new_blog.title
        return {"title": title, "detail": "Successfully created the blog"}

    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))

@router.post("/blog/{blog_id}/like")
async def like_blog_route(
    blog_id: int,
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    try:
        return await like_unlike_blog(session=session, blog_id=blog_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while liking post {str(e)}")


@router.get("/blog")
async def get_all_blogs_route(
    search: str = Query(default=None),
    limit :int = Query(10, ge=1),
    offset: int = Query(0, ge=0), 
    session: AsyncSession = Depends(get_session)
):
    try:
        blogs = await get_all_blogs(session=session, search=search, limit=limit, offset=offset)
        return blogs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while getting blogs {str(e)}")


@router.get("/blog/liked", response_model=PaginatedResponse[BlogResponse])
async def get_liked_blog_route(
    search: str = Query(default=None),
    limit :int = Query(10, ge=1),
    offset: int = Query(0, ge=0), 
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    try:
        return await get_liked_blogs(session=session, search=search, limit=limit, offset=offset, user_id=current_user.id) # type: ignore

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")



@router.get("/blog/mine")
async def get_mine_blog_route(
    search: str | None = Query(default=None),
    limit:int = Query(10, ge=1),
    offset:int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user)
):
    try:

        return await get_current_user_blog(session=session, search=search, limit=limit, offset=offset, current_user=current_user.id)
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@router.get("/blog/{blog_id}", response_model=BlogContentResponse)
async def get_specefic_blog_route(
    blog_id: int, 
    session: AsyncSession = Depends(get_session)
):
    try:
        blog = await get_blog_by_id(session=session, blog_id=blog_id)
        
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        return blog
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")



@router.patch("/blog/{blogs_id}")
async def update_blog_route(
    blog_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    thumbnail: UploadFile | None = None ,
    session: AsyncSession =  Depends(get_session), 
    current_user: CurrentUserRead = Depends(get_current_user)
):
    try:
        return await update_blog(session=session, blog_id=blog_id, title=title, content=content, thumbnail=thumbnail, current_user=current_user.id, thumbnail_path=thumbnail_path)
        
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.delete("/blog/{blog_id}")
async def delete_blog_route(
    blog_id:int,
    session: AsyncSession =  Depends(get_session), 
    current_user:CurrentUserRead = Depends(get_current_user)
):
    try:
        title = await delete_blog(session=session, blog_id=blog_id, current_user=current_user.id)
        return {"title": title, "detail": "Successfully deleted blog"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
