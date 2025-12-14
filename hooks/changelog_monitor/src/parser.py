"""Parse Claude Code changelog for versions and features."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger()


@dataclass
class VersionEntry:
    """A version entry from the changelog."""

    version: str
    date: str | None = None
    features: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    breaking: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)


def parse_changelog(content: str) -> list[VersionEntry]:
    """Parse changelog content into structured version entries."""
    versions: list[VersionEntry] = []
    current: VersionEntry | None = None
    current_section: str = "other"

    for line in content.split("\n"):
        line = line.strip()

        # Match version headers: ## [1.0.62] - 2025-12-12 or ## 1.0.62
        version_match = re.match(r"##\s*\[?(\d+\.\d+\.\d+)\]?\s*(?:-\s*(.+))?", line)
        if version_match:
            if current:
                versions.append(current)
            current = VersionEntry(
                version=version_match.group(1),
                date=version_match.group(2) if version_match.group(2) else None,
            )
            current_section = "other"
            continue

        # Match section headers: ### Added, ### Fixed, ### Breaking, etc.
        section_match = re.match(r"###\s*(.+)", line)
        if section_match:
            section = section_match.group(1).lower()
            if "add" in section or "new" in section or "feature" in section:
                current_section = "features"
            elif "fix" in section or "bug" in section:
                current_section = "fixes"
            elif "break" in section or "remov" in section or "deprecat" in section:
                current_section = "breaking"
            else:
                current_section = "other"
            continue

        # Match list items
        if current and line.startswith("- "):
            item = line[2:].strip()
            if current_section == "features":
                current.features.append(item)
            elif current_section == "fixes":
                current.fixes.append(item)
            elif current_section == "breaking":
                current.breaking.append(item)
            else:
                current.other.append(item)

    # Don't forget the last entry
    if current:
        versions.append(current)

    log.debug("parsed_changelog", version_count=len(versions))
    return versions


def get_versions_since(versions: list[VersionEntry], since_version: str | None) -> list[VersionEntry]:
    """Get all versions newer than the specified version."""
    if not since_version:
        return versions

    # Parse version for comparison
    def version_tuple(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("."))

    try:
        since_tuple = version_tuple(since_version)
    except ValueError:
        return versions

    new_versions = []
    for entry in versions:
        try:
            entry_tuple = version_tuple(entry.version)
            if entry_tuple > since_tuple:
                new_versions.append(entry)
        except ValueError:
            continue

    return new_versions


def extract_keywords(text: str) -> list[str]:
    """Extract relevant keywords from changelog entry."""
    keywords = []

    # Feature keywords
    keyword_patterns = [
        (r"\bhook\b", "hooks"),
        (r"\bevent\b", "events"),
        (r"\btrigger\b", "triggers"),
        (r"\btool\b", "tools"),
        (r"\bMCP\b", "mcp"),
        (r"\bagent\b", "agents"),
        (r"\bskill\b", "skills"),
        (r"\bcommand\b", "commands"),
        (r"\bslash command\b", "slash-commands"),
        (r"\bAPI\b", "api"),
        (r"\bconfiguration\b", "config"),
        (r"\bsettings\b", "settings"),
    ]

    text_lower = text.lower()
    for pattern, keyword in keyword_patterns:
        if re.search(pattern, text_lower):
            keywords.append(keyword)

    return list(set(keywords))
