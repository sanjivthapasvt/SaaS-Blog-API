from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi.exceptions import HTTPException

from app.admin.schema import BlogCreate, BlogUpdate, TagCreate, TagUpdate
from app.blogs.models import Blog, Comment, Tag


# BLOGS
async def list_blogs(
    search: str | None, limit: int, offset: int, session: AsyncSession
):
    query = select(Blog)
    total_query = select(func.count()).select_from(Blog)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    query = query.order_by(desc(Blog.created_at)) # type: ignore

    total = await session.execute(total_query)
    total_result = total.scalar_one()

    blogs = await session.execute(query.limit(limit).offset(offset))
    blogs_result = blogs.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": blogs_result,
    }


async def get_blog(session: AsyncSession, blog_id: int):
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found!")
    return blog


async def create_blog(session: AsyncSession, blog_data: BlogCreate, author_id: int):
    blog = Blog(
        title=blog_data.title,
        content=blog_data.content,
        is_public=blog_data.is_public,
        thumbnail_url=blog_data.thumbnail_url,
        author=author_id,
    )
    session.add(blog)
    await session.commit()
    await session.refresh(blog)
    return blog


async def update_blog(session: AsyncSession, blog_id: int, blog_data: BlogUpdate):
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found!")

    for key, value in blog_data.model_dump(exclude_unset=True).items():
        setattr(blog, key, value)

    await session.commit()
    await session.refresh(blog)
    return blog


async def delete_blog(session: AsyncSession, blog_id: int) -> str:
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found!")

    title = blog.title
    await session.delete(blog)
    await session.commit()
    return title


# TAGS
async def list_tags(
    search: str | None, limit: int, offset: int, session: AsyncSession
):
    query = select(Tag)
    total_query = select(func.count()).select_from(Tag)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Tag.title).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    total = await session.execute(total_query)
    total_result = total.scalar_one()

    tags = await session.execute(query.limit(limit).offset(offset))
    tags_result = tags.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": tags_result,
    }


async def create_tag(session: AsyncSession, tag_data: TagCreate):
    exists = await session.execute(
        select(Tag).where(Tag.title == tag_data.title)
    )
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(title=tag_data.title)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def update_tag(session: AsyncSession, tag_id: int, tag_data: TagUpdate):
    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found!")

    if tag_data.title:
        exists = await session.execute(
            select(Tag).where(Tag.title == tag_data.title)
        )
        if exists.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Tag already exists with this name",
            )
        tag.title = tag_data.title

    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(session: AsyncSession, tag_id: int):
    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found!")

    title = tag.title
    await session.delete(tag)
    await session.commit()
    return title


# COMMENTS
async def list_comments(
    search: str | None, limit: int, offset: int, session: AsyncSession
):
    query = select(Comment)
    total_query = select(func.count()).select_from(Comment)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Comment.content).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    query = query.order_by(desc(Comment.created_at))

    total = await session.execute(total_query)
    total_result = total.scalar_one()

    comments = await session.execute(query.limit(limit).offset(offset))
    comments_result = comments.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": comments_result,
    }


async def get_comment(session: AsyncSession, comment_id: int):
    comment = await session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found!")
    return comment


async def delete_comment(session: AsyncSession, comment_id: int):
    comment = await session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found!")

    await session.delete(comment)
    await session.commit()
    return "Comment deleted"
