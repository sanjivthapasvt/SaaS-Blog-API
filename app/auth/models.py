from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class VerificationToken(SQLModel, table=True):
    """Model for storing email verification and password reset tokens"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    token: str = Field(index=True, unique=True)
    token_type: str = Field(index=True)  # "email_verification" or "password_reset"
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = Field(default=False)
