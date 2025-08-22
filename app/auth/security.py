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


def check_password_strength(password: str) -> tuple[bool, list[str]]:
    reasons = []

    if len(password) < 8:
        reasons.append("Password must be at least 8 characters long.")

    has_upper = has_lower = has_digit = has_special = False
    specials = set('!@#$%^&*(),.?":{}|<>')

    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        elif ch in specials:
            has_special = True

    if not has_upper:
        reasons.append("Password must contain at least one uppercase letter.")
    if not has_lower:
        reasons.append("Password must contain at least one lowercase letter.")
    if not has_digit:
        reasons.append("Password must contain at least one digit.")
    if not has_special:
        reasons.append("Password must contain at least one special character.")

    return (len(reasons) == 0, reasons)
