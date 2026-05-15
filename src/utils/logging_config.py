"""Loguru logging configuration for the application."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """Configure Loguru to write to stdout and a rotating log file.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
    """
    logger.remove()

    # Stdout handler
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File handler with rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
