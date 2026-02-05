from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.crud.blog_admin import (create_blog, create_tag, delete_blog,
                                       delete_comment, delete_tag, get_blog,
                                       get_comment, list_blogs, list_comments,
                                       list_tags, update_blog, update_tag)
from app.admin.schema import (BlogCreate, BlogDetail, BlogUpdate, CommentDetail,
                              TagCreate, TagDetail, TagUpdate)
from app.admin.utils import get_is_admin_user
from app.core.services.database import get_session
from app.models.schema import CommonParams, PaginatedResponse
from app.users.models import User
from app.utils.common_params import get_common_params
from app.utils.logger import logger
from app.utils.rate_limiter import user_identifier

router = APIRouter()


# BLOG ROUTES
@router.get(
    "/blogs",
    response_model=PaginatedResponse[BlogDetail],
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Blogs"],
)
async def list_blogs_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_blogs(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/blogs",
    response_model=BlogDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Blogs"],
)
async def create_blog_route(
    blog_data: BlogCreate,
    current_user: User = Depends(get_is_admin_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        new_blog = await create_blog(session, blog_data, current_user.id)
        logger.info(f"Admin {current_user.id} created new blog: {new_blog.id} - {new_blog.title}")
        return new_blog
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating blog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/blogs/{blog_id}",
    response_model=BlogDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Blogs"],
)
async def get_blog_route(
    blog_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_blog(session, blog_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/blogs/{blog_id}",
    response_model=BlogDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Blogs"],
)
async def update_blog_route(
    blog_id: int,
    blog_data: BlogUpdate,
    session: AsyncSession = Depends(get_session),
):
    try:
        updated_blog = await update_blog(session, blog_id, blog_data)
        logger.info(f"Admin updated blog {blog_id}. Data: {blog_data.model_dump(exclude_unset=True)}")
        return updated_blog
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating blog {blog_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/blogs/{blog_id}",
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Blogs"],
)
async def delete_blog_route(
    blog_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        title = await delete_blog(session, blog_id)
        logger.info(f"Admin deleted blog {blog_id} ('{title}')")
        return f"Deleted blog '{title}' successfully!"
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blog {blog_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# TAG ROUTES
@router.get(
    "/tags",
    response_model=PaginatedResponse[TagDetail],
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Tags"],
)
async def list_tags_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_tags(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tags",
    response_model=TagDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Tags"],
)
async def create_tag_route(
    tag_data: TagCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        new_tag = await create_tag(session, tag_data)
        logger.info(f"Admin created tag: {new_tag.title}")
        return new_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/tags/{tag_id}",
    response_model=TagDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Tags"],
)
async def update_tag_route(
    tag_id: int,
    tag_data: TagUpdate,
    session: AsyncSession = Depends(get_session),
):
    try:
        updated_tag = await update_tag(session, tag_id, tag_data)
        logger.info(f"Admin updated tag {tag_id}. Data: {tag_data.model_dump(exclude_unset=True)}")
        return updated_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/tags/{tag_id}",
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Tags"],
)
async def delete_tag_route(
    tag_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        title = await delete_tag(session, tag_id)
        logger.info(f"Admin deleted tag {tag_id} ('{title}')")
        return f"Deleted tag '{title}' successfully!"
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# COMMENT ROUTES
@router.get(
    "/comments",
    response_model=PaginatedResponse[CommentDetail],
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Comments"],
)
async def list_comments_route(
    params: CommonParams = Depends(get_common_params),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await list_comments(
            session=session,
            search=params.search,
            limit=params.limit,
            offset=params.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/comments/{comment_id}",
    response_model=CommentDetail,
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Comments"],
)
async def get_comment_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await get_comment(session, comment_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/comments/{comment_id}",
    dependencies=[Depends(get_is_admin_user)],
    tags=["Admin - Comments"],
)
async def delete_comment_route(
    comment_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(f"Admin deleting comment {comment_id}")
        return await delete_comment(session, comment_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
