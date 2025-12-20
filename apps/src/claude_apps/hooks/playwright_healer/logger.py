import sys
import json
import structlog
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .paths import get_config, get_log_path, get_error_log_path


_logger = None


def _read_existing_entries(file_path: Path) -> List[Dict[str, Any]]:
    """Read existing JSON array from file, returning empty list on any error."""
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding='utf-8').strip()
        if not content:
            return []

        data = json.loads(content)
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, IOError):
        return []


def _write_json_array_entry(file_path: Path, entry: Dict[str, Any]) -> None:
    """Append an entry to a JSON array file with pretty-printing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    entries = _read_existing_entries(file_path)
    entries.append(entry)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write('\n')


def setup_logger() -> Optional[structlog.BoundLogger]:
    """Configure and return structlog logger."""
    global _logger

    if _logger is not None:
        return _logger

    config = get_config()

    if not config.get("log_enabled", True):
        return None

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _logger = structlog.get_logger()

    return _logger


def log_healing_event(
    session_id: str,
    event_type: str,
    tool_name: str,
    **kwargs
) -> None:
    """Log a healing event to file."""
    try:
        setup_logger()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "playwright_healing",
            "session_id": session_id,
            "event_type": event_type,
            "tool_name": tool_name,
            **kwargs
        }

        log_path = get_log_path(session_id, event_type)
        _write_json_array_entry(log_path, log_entry)

    except Exception as e:
        sys.stderr.write(f"[playwright_healer] Failed to log healing event: {e}\n")
        sys.stderr.flush()


def log_error(error_message: str, session_id: str = "unknown", **context) -> None:
    """Log an error event to file."""
    try:
        setup_logger()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "session_id": session_id,
            "error_message": error_message,
            **context
        }

        error_path = get_error_log_path(session_id)
        _write_json_array_entry(error_path, log_entry)

    except Exception as e:
        sys.stderr.write(f"[playwright_healer] Failed to log error: {e}\n")
        sys.stderr.flush()
