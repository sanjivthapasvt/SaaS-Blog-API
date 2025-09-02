import asyncio
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.blogs.models import Blog
from app.core.services.celery_app import celery_app
from app.core.services.database import get_session


def calculate_momentum_factor(blog) -> float:
    """
    Calculate momentum factor for trending score
    """
    # Time decay factor
    hours_since_creation = (
        datetime.now(timezone.utc) - blog.created_at
    ).total_seconds() / 3600
    time_decay = 2 ** (-hours_since_creation / 12)

    # Simple engagement boost based on absolute score
    engagement_boost = min(1 + (blog.engagement_score / 100), 3.0)

    # Combine factors
    momentum_factor = time_decay * engagement_boost

    return max(0.1, min(momentum_factor, 10.0))


async def _update_trending_score():
    """Async function for updating Trending score"""
    async for session in get_session():
        try:
            # Get blogs with recent activity
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await session.execute(
                select(Blog).where(Blog.created_at >= cutoff)
            )
            recent_blogs = result.scalars().all()

            for blog in recent_blogs:
                # Complex trending calculation
                hours_since_creation = (
                    datetime.now(timezone.utc) - blog.created_at
                ).total_seconds() / 3600
                engagement_velocity = blog.engagement_score / max(
                    hours_since_creation, 1
                )

                blog.trending_score = engagement_velocity * calculate_momentum_factor(
                    blog
                )
                session.add(blog)

            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _update_popular_score():
    """Async function for updating Popular score"""
    async for session in get_session():
        try:
            result = await session.execute(select(Blog))
            all_blogs = result.scalars().all()

            for blog in all_blogs:
                # Time-decayed popularity
                days_old = (datetime.now(timezone.utc) - blog.created_at).days
                decay_factor = 1 / (1 + days_old * 0.1)  # Gradual decay

                blog.popular_score = blog.engagement_score * decay_factor
                session.add(blog)

            await session.commit()
        except Exception:
            await session.rollback()
            raise


@celery_app.task
def update_trending_scores():
    """Celery task to update trending score"""
    asyncio.run(_update_trending_score())


@celery_app.task
def update_popular_scores():
    """Celery task to update popular scores"""
    asyncio.run(_update_popular_score())
