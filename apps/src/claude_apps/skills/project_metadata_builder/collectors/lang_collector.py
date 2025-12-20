"""
Language detection collector.
"""
from collections import Counter
from pathlib import Path

from loguru import logger

from ..schema import Languages

# File extension to language mapping
EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C",
    ".hpp": "C++",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".r": "R",
    ".R": "R",
    ".lua": "Lua",
    ".pl": "Perl",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".cache",
    "coverage",
    ".coverage",
    ".idea",
    ".vscode",
}


def collect_languages(project_path: Path) -> Languages:
    """Detect languages used in a project."""
    languages = Languages()
    lang_bytes: Counter[str] = Counter()

    def should_ignore(path: Path) -> bool:
        """Check if path should be ignored."""
        for part in path.parts:
            if part in IGNORE_DIRS or part.startswith("."):
                return True
        return False

    try:
        for file_path in project_path.rglob("*"):
            if not file_path.is_file():
                continue
            if should_ignore(file_path.relative_to(project_path)):
                continue

            ext = file_path.suffix.lower()
            if ext in EXTENSION_MAP:
                try:
                    size = file_path.stat().st_size
                    lang_bytes[EXTENSION_MAP[ext]] += size
                except Exception:
                    continue

        total_bytes = sum(lang_bytes.values())
        if total_bytes > 0:
            # Calculate percentages
            for lang, bytes_count in lang_bytes.most_common():
                languages.all[lang] = bytes_count / total_bytes

            # Set primary language
            if languages.all:
                languages.primary = next(iter(languages.all))

        logger.info(
            f"Detected {len(languages.all)} languages, "
            f"primary={languages.primary}"
        )

    except Exception as e:
        logger.error(f"Error detecting languages: {e}")

    return languages
