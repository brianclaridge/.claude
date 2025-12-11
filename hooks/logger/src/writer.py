import json
from pathlib import Path
from typing import Dict, Any, List


def ensure_directory(file_path: Path) -> None:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def read_existing_entries(file_path: Path) -> List[Dict[str, Any]]:
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


def write_log_entry(file_path: Path, hook_data: Dict[str, Any]) -> None:
    """Write a log entry to a JSON array file with pretty-printing."""
    try:
        ensure_directory(file_path)

        entries = read_existing_entries(file_path)
        entries.append(hook_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
            f.write('\n')

    except Exception:
        pass
