import asyncio
import json
from typing import Dict, Set

from app.utils.logger import logger


# Server-Sent Event Manager
class SSEManager:
    def __init__(self):
        self.connections: Dict[int, Set[asyncio.Queue]] = {}

    def add_connection(self, user_id: int, queue: asyncio.Queue):
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(queue)

    def remove_connection(self, user_id: int, queue: asyncio.Queue):
        if user_id in self.connections:
            self.connections[user_id].discard(queue)
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def send_to_user(self, user_id: int, data: dict):
        if user_id in self.connections:
            message = json.dumps(data)
            for queue in self.connections[user_id].copy():
                try:
                    await queue.put(message)
                except:
                    # Remove broken connections
                    self.connections[user_id].discard(queue)

    async def start_redis_listener(self, redis_manager):
        """Listen for Redis pub/sub messages and forward to SSE connections"""
        try:
            pubsub = await redis_manager.psubscribe("notifications:*")
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        # Extract user_id from channel name: notifications:123
                        channel = message["channel"]
                        user_id = int(channel.split(":")[-1])

                        # Parse notification data
                        notification_data = json.loads(message["data"])

                        # Send to all SSE connections for this user
                        await self.send_to_user(user_id, notification_data)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")


sse_manager = SSEManager()
