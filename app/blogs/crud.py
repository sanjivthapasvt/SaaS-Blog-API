from datetime import datetime, timezone

from aiosqlite import IntegrityError
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import and_, col, func, insert, select, delete

from app.blogs.models import Blog, BlogTagLink, Comment, Tag
from app.models.blog_like_link import BlogLikeLink
from app.notifications.models import Notification, NotificationType
from app.notifications.notification_service import create_notification
from app.users.models import User, UserFollowLink
from app.users.schema import CurrentUserRead
from app.utils.remove_image import remove_image
from app.utils.save_image import save_image


async def create_new_blog(
    session: AsyncSession,
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
    followers_result = followers.scalars().all()

    # creating notificatoin for all users in single query
    notifications = [
        {
            "owner_id": follower_ids,
            "triggered_by_user_id": new_blog.author,
            "blog_id": new_blog.id,
            "notification_type": NotificationType.NEW_BLOG,
            "message": f"{current_user.full_name} uploaded new blog {new_blog.title}",
        }
        for follower_ids in followers_result
    ]

    if notifications:  # insert if there are followers
        await session.execute(insert(Notification).values(notifications))
        await session.commit()

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


async def like_unlike_blog(
    session: AsyncSession, blog_id: int, current_user: CurrentUserRead
):
    """
    Toggle like/unlike status for a blog by the current user.

    Raises 404 if blog not found.

    Returns dict with action result message.
    """

    result = await session.execute(
        select(BlogLikeLink).where(
            (BlogLikeLink.blog_id == blog_id)
            & (BlogLikeLink.user_id == current_user.id)
        )
    )

    existing_like = result.scalars().first()

    if existing_like:
        blog = await session.get(Blog, blog_id)
        
        if not blog:
            raise HTTPException(status_code=404, detail="Blog doesn't exist")
        
        await session.delete(existing_like)
        # Delete notification if not self-like
        if current_user.id != blog.author:
            await session.execute(
                delete(Notification).where(
                    and_(
                        Notification.owner_id == blog.author,
                        Notification.blog_id == blog.id,
                        Notification.notification_type == NotificationType.LIKE,
                        Notification.triggered_by_user_id == current_user.id
                    )
                )
            )
        await session.commit()
        return {"detail": "removed from liked blogs"}

    try:
        # get blog info for notification
        blog = await session.get(Blog, blog_id)

        if not blog:
            raise HTTPException(status_code=404, detail="Blog doesn't exist")

        # create like link
        new_link = BlogLikeLink(blog_id=blog_id, user_id=current_user.id)
        session.add(new_link)
        await session.commit()

        # create notification only if not self-like
        if current_user.id != blog.author:
            await create_notification(
                session=session,
                owner_id=blog.author,
                triggered_by_user_id=current_user.id,
                blog_id=blog.id,
                notification_type=NotificationType.LIKE,
                message=f"{current_user.full_name} liked your blog {blog.title}",
            )
        return {"detail": "added to liked blogs"}

    except IntegrityError:
        # race condition: like was created by another request
        await session.rollback()
        return {"detail": "already liked"}


async def get_all_blogs(
    session: AsyncSession, search: str | None, limit: int, offset: int
):
    """
    Retrieve paginated list of blogs, optionally filtered by a search term in the title.

    Returns a dict with total count, pagination info, and blog data.
    """
    query = select(Blog)
    total_query = select(func.count()).select_from(Blog)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    blogs = await session.execute(query.offset(offset).limit(limit).options(selectinload(Blog.tags)))  # type: ignore
    blogs_result = blogs.scalars().all()

    total = await session.execute(total_query)
    total_result = total.scalars().one()

    return blogs_result, total_result


async def get_blog_by_id(session: AsyncSession, blog_id: int) -> Blog | None:
    """
    Get a blog by ID.

    Raises 404 if not found.

    Returns Blog instance.
    """
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


async def get_liked_blogs(
    session: AsyncSession, search: str | None, limit: int, offset: int, user_id: int
):
    """
    Retrieve paginated blogs liked by a user, optionally filtered by a search term.

    Returns a dict with total count, pagination info, and blog data.
    """
    
    base_query = (
        select(Blog)
        .join(BlogLikeLink, col(Blog.id) == col(BlogLikeLink.blog_id))
        .where(col(BlogLikeLink.user_id) == user_id)
    )
    
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(
            func.lower(col(Blog.title)).like(search_term)
        )
    
    # Count query
    total_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(total_query)
    total_count = total_result.scalar() or 0
    
    # Data query with column reference
    blogs_query = (
        base_query
        .options(selectinload(getattr(Blog, 'tags')))
        .limit(limit)
        .offset(offset)
        .order_by(col(Blog.id)) 
    )
    
    blogs_result = await session.execute(blogs_query)
    blogs = blogs_result.scalars().all()
    
    return blogs, total_count


async def get_user_blogs(
    session: AsyncSession, search: str | None, limit: int, offset: int, user_id: int
):
    """
    Retrieve paginated blogs authored by a specific user, optionally filtered by a search term.

    Returns a dict with total count, pagination info, and blog data.
    """
    if not await session.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    query = select(Blog).where(Blog.author == user_id)
    total_query = select(func.count()).select_from(Blog).where(Blog.author == user_id)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)

        query = query.where(condition)
        total_query = total_query.where(condition)

    blogs = await session.execute(query.limit(limit).offset(offset).options(selectinload(getattr(Blog, 'tags'))))
    blogs_result = blogs.scalars().all()

    total = await session.execute(total_query)
    total_result = total.scalars().one()

    return blogs_result, total_result


async def update_blog(
    blog_id: int,
    title: str | None,
    content: str | None,
    thumbnail: UploadFile | None,
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

    if not (title or thumbnail or content):
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
    await session.execute(delete(Comment).where(Comment.blog_id == blog_id)) # type: ignore
    # Delete the blog itself
    await session.delete(blog)
    await session.commit()

    return blog.title


#####################
####Comments CRUD####
#####################


async def create_comment(
    session: AsyncSession, blog_id: int, content: str, commented_by: int
) -> Comment:
    """
    Create a comment on a blog post.

    Returns the created Comment instance.
    """
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="The field cannot be empty")
    
    
    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    new_comment = Comment(blog_id=blog_id, content=content, commented_by=commented_by)

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return new_comment


async def read_comments(blog_id: int, session: AsyncSession):
    """
    Retrieve all comments for a given blog.

    Raises 404 if blog not found.

    Returns list of Comment instances.
    """
    if not await session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    comments = await session.execute(select(Comment).where(Comment.blog_id == blog_id))
    return comments.scalars().all()


async def update_comment(
    comment_id: int, content: str, session: AsyncSession, current_user: int
):
    """
    Update content of a comment owned by the current user.

    Raises 404 if comment not found, 403 if user is not the owner.

    Returns dict confirming success.
    """
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="The field cannot be empty")
    
    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.commented_by != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of the comment"
        )

    comment.content = content
    comment.last_modified = datetime.now(timezone.utc)
    session.add(comment)
    await session.commit()

    return {"detail": "Successfully updated comment"}


async def delete_comment(comment_id: int, session: AsyncSession, current_user: int):
    """
    Delete a comment owned by the current user.

    Raises 404 if comment not found, 403 if user is not the owner.

    Returns dict confirming success.
    """
    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.commented_by != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of the comment"
        )

    await session.delete(comment)
    await session.commit()
    return {"detail": "Successfully deleted comment"}
