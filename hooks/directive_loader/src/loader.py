from pathlib import Path
from typing import List, Dict
import sys
import time


def load_directives(directory_path: str) -> List[Dict[str, str]]:
    directives = []

    try:
        dir_path = Path(directory_path)

        if not dir_path.exists():
            print(f"Warning: Directory {directory_path} does not exist", file=sys.stderr)
            return directives

        if not dir_path.is_dir():
            print(f"Error: {directory_path} is not a directory", file=sys.stderr)
            return directives

        md_files = sorted(dir_path.glob("*.md"))

        for file_path in md_files:
            directive = read_directive(file_path)
            if directive:
                directives.append(directive)

    except Exception as e:
        print(f"Error loading directives: {e}", file=sys.stderr)

    return directives


def read_directive(file_path: Path) -> Dict[str, str]:
    try:
        content = file_path.read_text(encoding="utf-8").strip()
        return {
            "filename": file_path.name,
            "content": content
        }
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None