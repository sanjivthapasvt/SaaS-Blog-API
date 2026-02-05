import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.hashing import hash_password
from app.auth.models import VerificationToken
from app.auth.security import check_password_strength
from app.core.services.email import EmailService
from app.users.models import User
from app.utils.logger import logger


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


async def create_verification_token(
    session: AsyncSession,
    user_id: int,
    token_type: str,
    expires_in_hours: int = 24,
) -> str:
    """
    Create a new verification token for a user.

    Args:
        session: Database session
        user_id: ID of the user
        token_type: Type of token ("email_verification" or "password_reset")
        expires_in_hours: Token expiration time in hours

    Returns:
        The generated token string
    """
    # Invalidate any existing tokens of this type for the user
    existing_tokens = await session.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.token_type == token_type,
            VerificationToken.used == False,
        )
    )
    for token in existing_tokens.scalars().all():
        token.used = True

    # Create new token
    token = generate_token()
    verification_token = VerificationToken(
        user_id=user_id,
        token=token,
        token_type=token_type,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
    )

    session.add(verification_token)
    await session.commit()

    return token


async def verify_email(session: AsyncSession, token: str) -> dict:
    """
    Verify user's email using the provided token.

    Args:
        session: Database session
        token: Verification token

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Find the token
    result = await session.execute(
        select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.token_type == "email_verification",
        )
    )
    verification_token = result.scalars().first()

    if not verification_token:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if verification_token.used:
        raise HTTPException(status_code=400, detail="Token has already been used")

    expires_at = verification_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token has expired")

    # Get the user
    user_result = await session.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Mark user as verified and token as used
    user.is_verified = True
    verification_token.used = True

    await session.commit()

    return {"detail": "Email verified successfully"}


async def resend_verification_email(session: AsyncSession, email: str) -> dict:
    """
    Resend verification email to user.

    Args:
        session: Database session
        email: User's email address

    Returns:
        Success message
    """
    # Find user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        # Don't reveal if email exists
        return {"detail": "If this email is registered, a verification email will be sent"}

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Create new verification token
    token = await create_verification_token(
        session, user.id, "email_verification", expires_in_hours=24
    )

    # Send verification email
    await EmailService.send_verification_email(
        to=user.email,
        username=user.username or user.full_name,
        token=token,
    )

    return {"detail": "If this email is registered, a verification email will be sent"}


async def request_password_reset(session: AsyncSession, email: str) -> dict:
    """
    Request a password reset for the given email.

    Args:
        session: Database session
        email: User's email address

    Returns:
        Success message
    """
    # Find user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        # Don't reveal if email exists for security
        return {"detail": "If this email is registered, a password reset link will be sent"}

    # Users with Google OAuth only cannot reset password
    if user.google_id and not user.hashed_password:
        return {"detail": "If this email is registered, a password reset link will be sent"}

    # Create password reset token (expires in 1 hour)
    token = await create_verification_token(
        session, user.id, "password_reset", expires_in_hours=1
    )

    # Send password reset email
    await EmailService.send_password_reset_email(
        to=user.email,
        username=user.username or user.full_name,
        token=token,
    )

    logger.info(f"Password reset email sent to {email}")

    return {"detail": "If this email is registered, a password reset link will be sent"}


async def reset_password(
    session: AsyncSession, token: str, new_password: str
) -> dict:
    """
    Reset user's password using the provided token.

    Args:
        session: Database session
        token: Password reset token
        new_password: New password to set

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or password is weak
    """
    # Find the token
    result = await session.execute(
        select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.token_type == "password_reset",
        )
    )
    verification_token = result.scalars().first()

    if not verification_token:
        raise HTTPException(status_code=400, detail="Invalid password reset token")

    if verification_token.used:
        raise HTTPException(status_code=400, detail="Token has already been used")

    expires_at = verification_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token has expired")

    # Get the user
    user_result = await session.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check password strength
    strong, reasons = check_password_strength(new_password)
    if not strong:
        raise HTTPException(
            status_code=400,
            detail={"message": "Password is not strong enough", "reasons": reasons},
        )

    # Update password and mark token as used
    user.hashed_password = hash_password(new_password)
    verification_token.used = True

    await session.commit()

    logger.info(f"Password reset successful for user {user.username}")

    return {"detail": "Password reset successfully"}


async def send_verification_email_for_user(
    session: AsyncSession, user: User
) -> bool:
    """
    Create token and send verification email for a user.
    Used during registration.

    Args:
        session: Database session
        user: User object

    Returns:
        True if email was sent successfully
    """
    token = await create_verification_token(
        session, user.id, "email_verification", expires_in_hours=24
    )

    return await EmailService.send_verification_email(
        to=user.email,
        username=user.username or user.full_name,
        token=token,
    )
