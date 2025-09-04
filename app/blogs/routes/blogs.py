from typing import List

from fastapi import APIRouter, Depends, Form, Query, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependency import get_current_user
from app.blogs.crud.blogs import (create_new_blog, delete_blog, get_all_blogs,
                                  get_blog_by_id, get_popular_blogs, get_recommended_blogs, update_blog)
from app.blogs.schema import BlogContentResponse, BlogResponse
from app.core.services.database import get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.users.schema import CurrentUserRead
from app.utils.common_params import get_common_params
from app.utils.rate_limiter import user_identifier
from app.utils.save_image import save_image

router = APIRouter(tags=["Blogs - CRUD"])

thumbnail_path: str = "blogs/thumbnail"


@router.post(
    "/blogs",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def create_blog_route(
    request: Request,
    title: str = Form(..., max_length=500),
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
            request=request,
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


@router.get(
    "/blogs",
    response_model=PaginatedResponse[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=60, minutes=1, identifier=user_identifier))
    ],
)
async def get_all_blogs_route(
    params: CommonParams = Depends(get_common_params),
    tags: List[str] | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve all blogs with optional search and pagination."""
    try:
        blogs_result, total_result = await get_all_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
            tags=tags,
        )
        # validates response and set tags as list of strings
        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return PaginatedResponse[BlogResponse](
            total=total_result, limit=params.limit, offset=params.offset, data=data
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while getting blogs {str(e)}"
        )

@router.get(
    "/blogs/popular",
    response_model=PaginatedResponse[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=60, minutes=1, identifier=user_identifier))
    ],
)
async def get_popular_blogs_route(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve all blogs with optional search and pagination."""
    try:
        blogs_result, total_result = await get_popular_blogs(
            session=session,
            limit=limit,
            offset=offset
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
    "/blogs/{blog_id}/recommendation",
    response_model=List[BlogResponse],
    dependencies=[
        Depends(RateLimiter(times=60, minutes=1, identifier=user_identifier))
    ],
)
async def get_blog_recommendation_route(
    blog_id: int,
    limit: int = Query(default=10),
    session: AsyncSession = Depends(get_session),
):
    """Route to get recommended blog"""
    try:
        blogs_result = await get_recommended_blogs(
            session=session,
            limit=limit,
            blog_id=blog_id,
        )
        # validates response and set tags as list of strings
        data = [
            BlogResponse.model_validate(
                blog.model_copy(update={"tags": [tag.title for tag in blog.tags]})
            )
            for blog in blogs_result
        ]

        return data

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while getting blogs {str(e)}"
        )


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
    "/blogs/{blog_id}",
    dependencies=[
        Depends(RateLimiter(times=10, minutes=1, identifier=user_identifier))
    ],
)
async def update_blog_route(
    blog_id: int,
    title: str | None = Form(None),
    content: str | None = Form(None),
    is_pubic: bool | None = Form(True),
    thumbnail: UploadFile | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUserRead = Depends(get_current_user),
):
    """Update a blog post's title, content, or thumbnail."""
    try:
        await update_blog(
            session=session,
            blog_id=blog_id,
            title=title,
            content=content,
            thumbnail=thumbnail,
            is_public=is_pubic,
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
