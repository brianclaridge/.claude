"""Centralized loguru logging configuration."""

from pathlib import Path
from datetime import datetime
from loguru import logger
import sys

from config_reader import get_log_path


def setup_logging(
    script_name: str,
    log_dir: str | Path | None = None,
    subdirectory: str | None = "aws_sso",
) -> None:
    """
    Configure loguru for consistent logging across all scripts.

    Args:
        script_name: Name of the script (used in log filename)
        log_dir: Optional custom log directory (defaults to config.yml log_path)
        subdirectory: Optional subdirectory within log_dir (default: aws_sso)
    """
    if log_dir is None:
        log_dir = get_log_path()
    else:
        log_dir = Path(log_dir)

    if subdirectory:
        log_dir = log_dir / subdirectory

    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}_{script_name}.log"

    # Remove default handler
    logger.remove()

    # Console handler (INFO and above, simple format)
    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # File handler (DEBUG and above, detailed format)
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

    logger.debug(f"Logging to {log_file}")
