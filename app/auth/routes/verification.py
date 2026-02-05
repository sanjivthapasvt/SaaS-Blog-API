from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud.verification import (
    request_password_reset,
    resend_verification_email,
    reset_password,
    verify_email,
)
from app.auth.schemas import (
    EmailVerificationRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
)
from app.core.services.database import get_session

router = APIRouter(tags=["Auth - Verification"])


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=10, minutes=1))],
)
async def verify_email_route(
    request: EmailVerificationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Verify user's email address using the token sent via email.
    """
    try:
        return await verify_email(session, request.token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=3, minutes=1))],
)
async def resend_verification_route(
    request: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Resend email verification link to the user's email.
    """
    try:
        return await resend_verification_email(session, request.email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=3, minutes=1))],
)
async def forgot_password_route(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Request a password reset link to be sent to the user's email.
    """
    try:
        return await request_password_reset(session, request.email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=5, minutes=1))],
)
async def reset_password_route(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Reset user's password using the token from the password reset email.
    """
    try:
        return await reset_password(session, request.token, request.new_password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
