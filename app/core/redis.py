import redis.asyncio as redis
from fakeredis import FakeAsyncRedis


class RedisManager:
    def __init__(self):
        self.redis_client = None
        self.is_fake_redis = False

    async def connect(
        self, testing: bool = False, redis_url: str = "redis://localhost:6379"
    ):
        """Connect to Redis or FakeRedis for testing"""
        if testing:
            self.redis_client = FakeAsyncRedis(decode_responses=True)
            self.is_fake_redis = True
        else:
            self.redis_client = redis.from_url(
                redis_url, encoding="utf8", decode_responses=True
            )
            self.is_fake_redis = False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()

    async def publish(self, channel: str, message: str):
        """Publish message to Redis channel"""
        if self.redis_client:
            await self.redis_client.publish(channel, message)

    async def subscribe(self, channel: str):
        """Subscribe to Redis channel"""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        return None

    async def psubscribe(self, pattern: str):
        """Subscribe to Redis channel pattern"""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.psubscribe(pattern)
            return pubsub
        return None

    def get_client(self):
        """Get the Redis client for other uses (rate limiting, etc.)"""
        return self.redis_client

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.redis_client is not None


# Redis manager instance
redis_manager = RedisManager()
