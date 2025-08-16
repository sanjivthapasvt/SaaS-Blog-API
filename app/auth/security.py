import redis.asyncio as redis
from fastapi import Request

# Token blacklist


class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "blacklisted_token:"

    async def blacklist_token(self, jti: str, expire: int | None = None):
        """
        Blacklist a token.
        Args:
            jti: JWT ID
            expire: TTL in seconds
        """
        key = self.prefix + jti
        if expire and expire > 0:
            # expire parameter
            await self.redis.set(key, "1", ex=expire)
        else:
            # set without expiration
            await self.redis.set(key, "1")

    async def is_blacklisted(self, jti: str) -> bool:
        # check if token is blacklisted
        key = self.prefix + jti
        exists = await self.redis.exists(key)
        return exists == 1

    async def remove_token(self, jti: str):
        # Remove token from blacklist
        key = self.prefix + jti
        await self.redis.delete(key)


async def get_token_blacklist(request: Request) -> TokenBlacklist:
    return request.app.state.token_blacklist
