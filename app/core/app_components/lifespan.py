import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.auth.security import TokenBlacklist
from app.core.services.database import init_db
from app.core.services.redis import redis_manager
from app.realtime.manager import sse_manager

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events configuration"""
    testing = os.environ.get("TESTING") == "1"
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Connect Redis using the manager
    await redis_manager.connect(testing=testing, redis_url=redis_url)
    redis_connection = redis_manager.get_client()

    # Initialize FastAPI Limiter
    await FastAPILimiter.init(redis_connection)
    await init_db()

    # store redis in app.state
    app.state.redis = redis_connection
    app.state.token_blacklist = TokenBlacklist(redis_connection)  # type: ignore
    app.state.redis_manager = redis_manager

    # Start SSE Redis listener (if not testing or if you want to test SSE)
    listener_task = None
    if not testing or os.environ.get("TEST_SSE") == "1":
        listener_task = asyncio.create_task(
            sse_manager.start_redis_listener(redis_manager)
        )

    yield

    # Cleanup
    if listener_task:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass

    await redis_manager.disconnect()
