import json
import structlog
from pathlib import Path
from typing import Dict, Any, List

from .paths import get_hook_config, get_log_path, get_error_log_path


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


def setup_logger() -> structlog.BoundLogger | None:
    """Configure and return structlog logger instance."""
    global _logger

    if _logger is not None:
        return _logger

    config = get_hook_config()

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


def log_directive_event(
    session_id: str,
    event_name: str,
    directive_count: int,
    directives: List[Dict[str, str]],
    load_time_ms: float,
    source_directory: str
) -> None:
    try:
        logger = setup_logger()
        if not logger:
            return

        log_entry = {
            "event": "directives_loaded",
            "session_id": session_id,
            "hook_event_name": event_name,
            "directive_count": directive_count,
            "directives": [d["filename"] for d in directives],
            "total_size_bytes": sum(len(d.get("content", "")) for d in directives),
            "load_time_ms": round(load_time_ms, 2),
            "source_directory": source_directory
        }

        log_path = get_log_path(session_id, event_name)
        _write_json_array_entry(log_path, log_entry)

    except Exception:
        pass


def log_error(error_message: str, session_id: str = "unknown", event_name: str = "Unknown", **context) -> None:
    try:
        logger = setup_logger()
        if not logger:
            return

        log_entry = {
            "event": "error",
            "session_id": session_id,
            "hook_event_name": event_name,
            "error_message": error_message,
            **context
        }

        error_path = get_error_log_path(session_id)
        _write_json_array_entry(error_path, log_entry)

    except Exception:
        pass


def log_summary(session_id: str, event_name: str, output_size: int, pretty: bool) -> None:
    try:
        logger = setup_logger()
        if not logger:
            return

        log_entry = {
            "event": "operation_complete",
            "session_id": session_id,
            "hook_event_name": event_name,
            "output_size_bytes": output_size,
            "pretty_printed": pretty
        }

        log_path = get_log_path(session_id, event_name)
        _write_json_array_entry(log_path, log_entry)

    except Exception:
        pass
