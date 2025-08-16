from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user
from app.blogs.crud import (create_new_blog, delete_blog, get_all_blogs,
                            get_blog_by_id, get_liked_blogs, like_unlike_blog,
                            update_blog)
from app.blogs.schema import BlogContentResponse, BlogResponse
from app.core.database import get_session
from app.models.schema import PaginatedResponse
from app.users.schema import CurrentUserRead
from app.utils.rate_limiter import user_identifier
from app.utils.save_image import save_image

router = APIRouter()

thumbnail_path: str = "blogs/thumbnail"


@router.post(
    "/blogs",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def create_blog_route(
    title: str = Form(...),
    content: str = Form(...),
    tags: str | None = Form(None),
    thumbnail: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    """Create a new blog post with optional tags and thumbnail."""
    try:

        thumbnail_url = await save_image(thumbnail, thumbnail_path)
        new_blog = await create_new_blog(
            session=session,
            title=title,
            thumbnail_url=thumbnail_url,
            content=content,
            current_user=current_user,
            tags=tags,
        )

        title = new_blog.title
        return JSONResponse(
            content={"detail": f"Successfully created blog {title}"},
            status_code=201,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))


@router.post(
    "/blogs/{blog_id}/like",
    dependencies=[
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier))
    ],
)
async def like_blog_route(
    blog_id: int,
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Toggle like status for a blog post."""
    try:
        return await like_unlike_blog(
            session=session, blog_id=blog_id, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while liking post {str(e)}"
        )


@router.get(
    "/blogs",
    response_model=PaginatedResponse[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=60, minutes=1, identifier=user_identifier))
    ],
)
async def get_all_blogs_route(
    search: str = Query(default=None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve all blogs with optional search and pagination."""
    try:
        blogs_result, total_result = await get_all_blogs(
            session=session, search=search, limit=limit, offset=offset
        )
        # validates response and set tags as list of strings
        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return PaginatedResponse[BlogResponse](
            total=total_result, limit=limit, offset=offset, data=data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while getting blogs {str(e)}"
        )


@router.get(
    "/blogs/liked",
    response_model=PaginatedResponse[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=30, minutes=1, identifier=user_identifier))
    ],
)
async def get_liked_blog_route(
    search: str = Query(default=None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    current_user: CurrentUserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve blogs liked by the current user."""
    try:
        blogs_result, total_result = await get_liked_blogs(
            session=session,
            search=search,
            limit=limit,
            offset=offset,
            user_id=current_user.id,
        )

        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return PaginatedResponse[BlogResponse](
            total=total_result, limit=limit, offset=offset, data=data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.get(
    "/blogs/{blog_id}",
    response_model=BlogContentResponse,
    dependencies=[
        Depends(RateLimiter(times=20, minutes=1, identifier=user_identifier))
    ],
)
async def get_specefic_blog_route(
    blog_id: int, session: AsyncSession = Depends(get_session)
):
    """Retrieve a specific blog post by ID."""
    try:
        blog = await get_blog_by_id(session=session, blog_id=blog_id)
        return blog

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.patch(
    "/blogs/{blogs_id}",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def update_blog_route(
    blog_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    thumbnail: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    """Update a blog post's title, content, or thumbnail."""
    try:
        updated_blog = await update_blog(
            session=session,
            blog_id=blog_id,
            title=title,
            content=content,
            thumbnail=thumbnail,
            current_user=current_user.id,
            thumbnail_path=thumbnail_path,
        )

        return JSONResponse(
            content={"detail": f"Successfully updated blog {title}"},
            status_code=200,
        )
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong{str(e)}")


@router.delete(
    "/blogs/{blog_id}",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def delete_blog_route(
    blog_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    """Delete a blog post by ID."""
    try:
        title = await delete_blog(
            session=session, blog_id=blog_id, current_user=current_user.id
        )
        return JSONResponse(
            content={"detail": f"Successfully deleted blog {title}"},
            status_code=200,
        )
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
