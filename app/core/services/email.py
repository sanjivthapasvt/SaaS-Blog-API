import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.services.config import settings
from app.utils.logger import logger


class EmailService:
    """Service for sending emails via SMTP"""

    @staticmethod
    async def send(to: str, subject: str, html: str) -> bool:
        """
        Send an email using SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML content of the email

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not settings.smtp_user or not settings.smtp_password:
            logger.warning("SMTP not configured, skipping email send")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
        message["To"] = to

        html_part = MIMEText(html, "html")
        message.attach(html_part)

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    @staticmethod
    async def send_verification_email(to: str, username: str, token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{settings.frontend_url}/verify-email?token={token}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to SaaS Blog!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username}!</h2>
                    <p>Thank you for registering. Please verify your email address to complete your registration.</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email</a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                </div>
                <div class="footer">
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await EmailService.send(to, "Verify your email - SaaS Blog", html)

    @staticmethod
    async def send_password_reset_email(to: str, username: str, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {username}!</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                    <div class="warning">
                        <strong>⚠️ This link will expire in 1 hour.</strong>
                    </div>
                </div>
                <div class="footer">
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                    <p>Your password will remain unchanged.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await EmailService.send(to, "Reset your password - SaaS Blog", html)