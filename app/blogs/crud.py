from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.blog_like_link import BlogLikeLink
from notifications.models import Notification, NotificationType
from notifications.notification_service import create_notfication
from users.schema import CurrentUserRead
from blogs.models import BlogTagLink, Comment, Blog, Tag
from utils.save_image import save_image

async def create_new_blog(session: AsyncSession, title: str, thumbnail_url: str | None, content: str, author: int, tags: str | None) -> Blog:
    new_blog = Blog(title=title, thumbnail_url=thumbnail_url, content=content, author=author)
    session.add(new_blog)
    await session.commit()
    await session.refresh(new_blog)

    if tags:
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


async def like_unlike_blog(session: AsyncSession, blog_id: int, current_user: CurrentUserRead):
    blog = await get_blog_by_id(session=session, blog_id=blog_id)
        
    if not blog:
        raise HTTPException(status_code=404, detail="Blog doesn't exist")

    result = await session.execute(
        select(BlogLikeLink).where(
            (BlogLikeLink.blog_id == blog.id) & (BlogLikeLink.user_id == current_user.id)
        )
    )

    is_liked = result.scalars().first()

    if is_liked:
        await session.delete(is_liked)
        await session.commit()
        return {"detail": "removed from liked blogs"}
        
    new_link = BlogLikeLink(blog_id=blog.id, user_id=current_user.id)
    session.add(new_link)
    await session.commit()
    await session.refresh(new_link)

    notification = await session.execute(
        select(Notification).where(
            (Notification.user_id == current_user.id) &
            (Notification.blog_id == blog.id) &
            (Notification.notification_type == NotificationType.LIKE)
        )
    )

    existing_notification = notification.scalars().first()

    if not existing_notification:
        await create_notfication(
            session=session,
            user_id = blog.author,
            notification_type=NotificationType.LIKE,
            message=f"{current_user.full_name} liked your blog {blog.title}"
        )
    return {"detail": "added to liked blogs"}


async def get_all_blogs(session: AsyncSession, search: str | None, limit: int, offset: int):
    query = select(Blog)
    total_query = select(func.count()).select_from(Blog)
        
    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    blogs = await session.execute(query.offset(offset).limit(limit).options(selectinload(Blog.tags))) # type: ignore
    blogs_result = blogs.scalars().all()

    total = await session.execute(total_query)
    total_result = total.scalars().one()
    
    result = [{
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "thumbnail_url": blog.thumbnail_url,
        "author": blog.author,
        "created_at": blog.created_at,
        "tags": [tag.title for tag in blog.tags]
    }for blog in blogs_result]

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": result,
    }

async def get_blog_by_id(session: AsyncSession, blog_id: int) -> Blog | None:
    return await session.get(Blog, blog_id)


async def get_liked_blogs(session: AsyncSession,search: str, limit: int, offset: int, user_id: int):
    raw_blogs_result = await session.execute(
        select(BlogLikeLink.blog_id).where(BlogLikeLink.user_id == user_id).limit(limit).offset(offset)
    )
    raw_blogs = raw_blogs_result.scalars().all()

    query = select(Blog).where(Blog.id.in_(raw_blogs))  # type: ignore
        
    total_query = select(func.count()).select_from(Blog)
        
    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    blogs = await session.execute(query.options(selectinload(Blog.tags))) # type: ignore
    blogs_result = blogs.scalars().all()

    total = await session.execute(total_query)
    total_result = total.scalars().one()
        
    result = [{
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "thumbnail_url": blog.thumbnail_url,
        "author": blog.author,
        "created_at": blog.created_at,
        "tags": [tag.title for tag in blog.tags]
    }for blog in blogs_result]

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": result,
    }


async def get_current_user_blog(session: AsyncSession, search: str | None , limit: int, offset: int, current_user: int):
    query = select(Blog).where(Blog.author == current_user)
    total_query = select(func.count()).select_from(Blog).where(Blog.author == current_user)
        
    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)

        query = query.where(condition)
        total_query = total_query.where(condition)

    blogs = await session.execute(query.limit(limit).offset(offset).options(selectinload(Blog.tags))) # type: ignore
    blogs_result = blogs.scalars().all()

    total = await session.execute(total_query)
    total_result = total.scalars().one()
                        
    result = [{
        "id": blog.id,
        "title": blog.title,
        "content": blog.content,
        "thumbnail_url": blog.thumbnail_url,
        "author": blog.author,
        "created_at": blog.created_at,
        "tags": [tag.title for tag in blog.tags]
    }for blog in blogs_result]

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": result,
    }



async def update_blog(
    blog_id: int, 
    title: str | None , 
    content: str | None, 
    thumbnail: UploadFile | None , 
    session: AsyncSession , 
    current_user:int,
    thumbnail_path: str
):
    
    blog = await get_blog_by_id(session=session, blog_id=blog_id)

    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    if blog.author != current_user:
        raise HTTPException(status_code=401, detail="You are not the owner of the blog")
        
    if not (title or thumbnail or content):
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")

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

    return {"detail": "Successfully updated blog contents"}
        

async def delete_blog(blog_id:int, session: AsyncSession, current_user: int ):
    blog = await get_blog_by_id(session=session, blog_id=blog_id)

    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
        
    if blog.author != current_user:
        raise HTTPException(status_code=401, detail="You are not the owner of the blog")

    title = blog.title
    await session.delete(blog)
    await session.commit()
        
    return title


#####################
####Comments CRUD####
#####################

async def create_comment(session: AsyncSession, blog_id: int, content: str, commented_by: int) -> Comment:
    new_comment = Comment(
        blog_id=blog_id,
        content=content, 
        commented_by=commented_by
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return new_comment

async def read_comments(blog_id:int, session: AsyncSession):
    if not (session.get(Blog, blog_id)):
        raise HTTPException(status_code=404, detail="Blog not found")
        
    comments = await session.execute(select(Comment).where(Comment.blog_id == blog_id))

    return comments.scalars().all()

async def update_comment(comment_id: int, content: str, session: AsyncSession, current_user: int):
    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()
        
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.commented_by != current_user:
        raise HTTPException(status_code=401, detail="You are not the owner of the comment")

    comment.content = content
    comment.last_modified = datetime.now(timezone.utc)
    session.add(comment)
    await session.commit()

    return {"detail": "Successfully updated comment"}


async def delete_comment(comment_id: int, session: AsyncSession, current_user: int):
    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.commented_by != current_user:
        raise HTTPException(status_code=401, detail="You are not the owner of the comment")
        
    await session.delete(comment)
    await session.commit()
    return {"detail": "Successfully deleted comment"}