from fastapi import Request

from app.auth.jwt_handler import decode_token


async def user_identifier(request: Request) -> str:
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return f"ip:{(request.client.host or 'unknown') if request.client else 'unknown'}"  # Fallback to IP

        token = auth_header.split(" ")[1]
        payload = decode_token(token, expected_type="access")
        if not payload:
            return f"ip:{(request.client.host or 'unknown') if request.client else 'unknown'}"

        sub = payload.get("sub")
        if not sub:
            return f"ip:{(request.client.host or 'unknown') if request.client else 'unknown'}"

        return f"user:{sub}"

    except Exception:
        return (
            f"ip:{(request.client.host or 'unknown') if request.client else 'unknown'}"
        )
