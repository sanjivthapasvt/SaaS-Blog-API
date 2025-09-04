import asyncio
from typing import List

from fastapi import HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import and_, col, delete, exists, func, select

from app.blogs.models import Blog, BlogTagLink, Comment, Tag
from app.notifications.models import NotificationType
from app.notifications.service import create_notifications
from app.users.models import User, UserFollowLink
from app.users.schema import CurrentUserRead
from app.utils.remove_image import remove_image
from app.utils.save_image import save_image


async def create_new_blog(
    session: AsyncSession,
    request: Request,
    title: str,
    thumbnail_url: str | None,
    content: str,
    current_user: CurrentUserRead,
    tags: str | None,
) -> Blog:
    """
    Create a new blog post with optional tags.

    Commits the blog and creates any new tags, linking them.

    Returns the created Blog instance.
    """
    if title.strip() == "":
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    if content.strip() == "":
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    new_blog = Blog(
        title=title,
        thumbnail_url=thumbnail_url,
        content=content,
        author=current_user.id,
    )

    session.add(new_blog)
    await session.commit()
    await session.refresh(new_blog)

    # listing followers of current user to create notification for them
    followers = await session.execute(
        select(UserFollowLink.follower_id).where(
            UserFollowLink.following_id == current_user.id
        )
    )
    followers_ids: List[int] = list(followers.scalars().all())

    await create_notifications(
        request=request,
        session=session,
        owner_ids=followers_ids,
        triggered_by_user_id=current_user.id,
        notification_type=NotificationType.NEW_BLOG,
        blog_id=new_blog.id,
        message=f"{current_user.full_name} uploaded new blog {new_blog.title}",
    )
    # creating notificatoin for all users in single query

    if tags:
        # split tags by #
        tag_list = [t.strip() for t in tags.split("#") if t.strip()]
        for tag in tag_list:
            result = await session.execute(select(Tag).where(Tag.title == tag))
            current_tag = result.scalars().first()
            if not current_tag:
                current_tag = Tag(title=tag)
                session.add(current_tag)
                await session.flush()

            new_link = BlogTagLink(blog_id=new_blog.id, tag_id=current_tag.id)
            session.add(new_link)

        await session.commit()
        await session.refresh(new_blog)

    return new_blog


async def get_all_blogs(
    session: AsyncSession,
    search: str | None,
    limit: int,
    offset: int,
    tags: List[str] | None,
):
    """
    Retrieve paginated list of blogs, optionally filtered by a search term in the title.

    Returns a dict with total count, pagination info, and blog data.
    """

    base_query = select(Blog).where(Blog.is_public == True)

    conditions = []

    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(func.lower(Blog.title).like(search_term))

    # Tag filtering
    if tags:
        # Create a subquery that checks if a blog has all required tags
        tag_subquery = (
            select(BlogTagLink.blog_id)
            .join(Tag, BlogTagLink.tag_id == Tag.id)  # type: ignore
            .where(and_(BlogTagLink.blog_id == Blog.id, col(Tag.title).in_(tags)))
            .group_by(BlogTagLink.blog_id)  # type: ignore
            .having(func.count(func.distinct(Tag.id)) == len(tags))
        )

        conditions.append(exists(tag_subquery))

    if conditions:
        filtered_query = base_query.where(and_(*conditions))
    else:
        filtered_query = base_query

    # main query with pagination
    blogs_query = (
        filtered_query.options(selectinload(Blog.tags))  # type: ignore
        .order_by(Blog.id)  # type: ignore
        .limit(limit)
        .offset(offset)
    )

    # create count query
    count_query = select(func.count(Blog.id)).where(  # type: ignore
        Blog.is_public == True
    )

    # apply conditions to count query
    if conditions:
        count_query = count_query.where(and_(*conditions))

    # Execute both queries concurrently
    blogs_result, total_result = await asyncio.gather(
        session.execute(blogs_query), session.execute(count_query)
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total

async def get_popular_blogs(
    session: AsyncSession,
    limit: int,
    offset: int,
):
    """
    Retrieve paginated list of popular blogs, optionally filtered by a search term in the title.

    Returns a dict with total count, pagination info, and blog data.
    """

    base_query = select(Blog).where((Blog.is_public)  & (Blog.engagement_score > 0))


    # main query with pagination
    blogs_query = (
        base_query.options(selectinload(Blog.tags))  # type: ignore
        .order_by(Blog.engagement_score)  # type: ignore
        .limit(limit)
        .offset(offset)
    )

    # create count query
    count_query = select(func.count(Blog.id)).where(  # type: ignore
        (Blog.is_public) & (Blog.engagement_score > 0)
    )

    # Execute both queries concurrently
    blogs_result, total_result = await asyncio.gather(
        session.execute(blogs_query), session.execute(count_query)
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total


async def get_blog_by_id(session: AsyncSession, blog_id: int) -> Blog | None:
    """
    Get a blog by ID.

    Raises 404 if not found.

    Returns Blog instance.
    """
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    blog.views += 1
    session.add(blog)
    await session.commit()
    return blog


async def list_user_blogs(
    session: AsyncSession,
    search: str | None,
    limit: int,
    offset: int,
    user_id: int,
    tags: List[str] | None,
):
    """
    Retrieve paginated blogs authored by a specific user, optionally filtered by a search term.

    Returns a dict with total count, pagination info, and blog data.
    """
    if not await session.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    base_query = select(Blog).where(Blog.author == user_id)

    conditions = []

    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(func.lower(Blog.title).like(search_term))

    # Tag filtering
    if tags:
        # Create a subquery that checks if a blog has all required tags
        tag_subquery = (
            select(BlogTagLink.blog_id)
            .join(Tag, BlogTagLink.tag_id == Tag.id)  # type: ignore
            .where(and_(BlogTagLink.blog_id == Blog.id, col(Tag.title).in_(tags)))
            .group_by(BlogTagLink.blog_id)  # type: ignore
            .having(func.count(func.distinct(Tag.id)) == len(tags))
        )

        conditions.append(exists(tag_subquery))

    if conditions:
        filtered_query = base_query.where(and_(*conditions))
    else:
        filtered_query = base_query

    # main query with pagination
    blogs_query = (
        filtered_query.options(selectinload(Blog.tags))  # type: ignore
        .order_by(Blog.id)  # type: ignore
        .limit(limit)
        .offset(offset)
    )

    # create count query
    count_query = select(func.count(Blog.id)).where(  # type: ignore
        Blog.author == user_id
    )

    # apply conditions to count query
    if conditions:
        count_query = count_query.where(and_(*conditions))

    # Execute both queries concurrently
    blogs_result, total_result = await asyncio.gather(
        session.execute(blogs_query), session.execute(count_query)
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total

async def get_recommended_blogs(
    session: AsyncSession,
    blog_id: int,
    limit: int = 5,
):
    """
    Recommend blogs based on shared tags with the current blog.
    Excludes the current blog from results.
    """
    # Fetch the current blog with its tags
    blog = await session.get(Blog, blog_id, options=[selectinload(Blog.tags)]) # type: ignore
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if not blog.tags:
        return []  # No tags, no recommendations

    # Collect tag ids of the current blog
    tag_ids = [tag.id for tag in blog.tags]

    # Query blogs that share tags with current blog
    query = (
        select(Blog)
        .join(BlogTagLink, Blog.id == BlogTagLink.blog_id) # type: ignore
        .where(
            BlogTagLink.tag_id.in_(tag_ids),  # has common tags # type: ignore
            Blog.id != blog.id,              # exclude current blog
            Blog.is_public == True
        )
        .options(selectinload(Blog.tags))  # eager load tags # type: ignore
        .group_by(Blog.id)                 # avoid duplicates # type: ignore
        .order_by(Blog.engagement_score.desc())  # prioritize popular # type: ignore
        .limit(limit)
    )

    result = await session.execute(query)
    recommended_blogs = result.scalars().all()
    return recommended_blogs

async def update_blog(
    blog_id: int,
    title: str | None,
    content: str | None,
    thumbnail: UploadFile | None,
    is_public: bool | None,
    session: AsyncSession,
    current_user: int,
    thumbnail_path: str,
):
    """
    Update title, content, and/or thumbnail of a blog owned by the current user.

    Raises 404 if blog not found, 401 if user is not the owner, and 400 if no update fields are provided.

    Returns dict confirming success.
    """
    blog = await session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.author != current_user:
        raise HTTPException(status_code=403, detail="You are not the owner of the blog")

    if not (title or thumbnail or content or is_public):
        raise HTTPException(
            status_code=400, detail="At least one field must be provided for update"
        )

    thumbnail_url = None

    if title:
        blog.title = title
    if thumbnail:
        thumbnail_url = await save_image(thumbnail, thumbnail_path)
        blog.thumbnail_url = thumbnail_url
    if content:
        blog.content = content
    if is_public:
        blog.is_public = is_public

    session.add(blog)
    await session.commit()
    await session.refresh(blog)
    return blog.title


async def delete_blog(blog_id: int, session: AsyncSession, current_user: int):
    """
    Delete a blog post owned by the current user.

    Raises 404 if blog not found, 401 if user is not the owner.

    Returns the deleted blog's title.
    """
    blog = await session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    if blog.author != current_user:
        raise HTTPException(status_code=403, detail="You are not the owner of the blog")

    # Remove thumbnail if exists
    if blog.thumbnail_url:
        await remove_image(blog.thumbnail_url)

    # Delete related comments
    await session.execute(delete(Comment).where(Comment.blog_id == blog_id))  # type: ignore
    # Delete the blog itself
    await session.delete(blog)
    await session.commit()

    return blog.title
