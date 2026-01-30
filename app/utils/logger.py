import logging
import sys
from typing import Optional

from app.core.services.config import settings


def setup_logger(name: str = "app_logger", force: bool = False) -> logging.Logger:
    """
    Configure and return the application logger.
    """
    logger = logging.getLogger(name)
    
    # Set log level from settings
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers and not force:
        return logger
    
    # Clear existing handlers if forcing reconfiguration
    if force:
        logger.handlers.clear()
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    try:
        from rich.logging import RichHandler
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False
        )
        logger.info("Using RichHandler for logging")
    except ImportError:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.debug("RichHandler not available, using StreamHandler")
    
    handler.setLevel(level)
    logger.addHandler(handler)
    
    return logger


logger = setup_logger()