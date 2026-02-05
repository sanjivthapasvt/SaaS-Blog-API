import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request details
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log response details
            logger.info(
                f"Response: {response.status_code} "
                f"Process Time: {process_time:.2f}ms"
            )
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request Failed: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Process Time: {process_time:.2f}ms"
            )
            raise
