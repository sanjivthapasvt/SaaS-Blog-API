import asyncio
import json

from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from app.auth.dependency import get_current_user_from_query
from app.realtime.manager import sse_manager
from app.users.models import User
from app.utils.logger import logger

router = APIRouter(prefix="/sse")


@router.get("/notifications")
async def stream_notifications(
    request: Request, current_user: User = Depends(get_current_user_from_query)
):
    """SSE endpoint for real-time notifications"""

    async def event_stream():
        # create queue for this connection
        queue = asyncio.Queue()

        # add connection to manager
        sse_manager.add_connection(current_user.id, queue)  # type: ignore

        try:
            # send connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to notifications"}),
            }

            # listen for messages
            while True:
                try:
                    # wait for new messages with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"event": "notification", "data": message}
                except asyncio.TimeoutError:
                    # send heartbeat to keep connection alive
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": "now"}),
                    }

                # check if client disconnected
                if await request.is_disconnected():
                    break

        except Exception as e:
            print(f"SSE connection error: {e}")
        finally:
            # clean up connection
            sse_manager.remove_connection(current_user.id, queue)  # type: ignore

    return EventSourceResponse(event_stream())
