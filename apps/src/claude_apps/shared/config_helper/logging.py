"""Standardized logging configuration for Claude Code hooks and skills."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    name: str,
    log_path: Optional[Path] = None,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
    format_string: Optional[str] = None,
) -> None:
    """Configure loguru logger for a hook or skill.

    Args:
        name: Name of the hook/skill for log identification
        log_path: Optional path to log file. If None, logs to stderr only.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate log files (e.g., "10 MB", "1 day")
        retention: How long to keep old log files
        format_string: Custom format string. Uses default if None.
    """
    # Remove default handler
    logger.remove()

    # Default format
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<cyan>{name}</cyan> | "
            "<level>{message}</level>"
        )

    # Add stderr handler
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
        colorize=True,
    )

    # Add file handler if path provided
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            format=format_string.replace("<green>", "").replace("</green>", "")
            .replace("<level>", "").replace("</level>", "")
            .replace("<cyan>", "").replace("</cyan>", ""),
            level=level,
            rotation=rotation,
            retention=retention,
            compression="gz",
        )


def get_logger():
    """Get the configured loguru logger instance.

    Returns:
        The loguru logger instance
    """
    return logger
