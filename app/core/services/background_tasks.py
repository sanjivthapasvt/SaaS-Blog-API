from app.utils.logger import logger
async def write_opt_email(email: str, otp: str):
    logger.debug(f"Sending otp email to: {email}")
    