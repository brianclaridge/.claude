"""Fetch and cache Claude Code changelog."""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import structlog

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
from config_helper import get_hook_config

log = structlog.get_logger()

# Cache configuration
CACHE_DIR = Path("/workspace/.claude/.data/cache")
CACHE_FILE = CACHE_DIR / "changelog.md"
CACHE_META = CACHE_DIR / "changelog.meta.json"
DEFAULT_TTL = 86400  # 24 hours in seconds

CHANGELOG_URL = "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md"


def get_cache_ttl() -> int:
    """Get cache TTL from config or use default."""
    try:
        hook_config = get_hook_config("changelog_monitor")
        hours = hook_config.get("cache_ttl_hours", 24)
        return hours * 3600
    except Exception:
        pass
    return DEFAULT_TTL


def is_cache_valid() -> bool:
    """Check if cached changelog is still valid."""
    if not CACHE_META.exists() or not CACHE_FILE.exists():
        return False

    try:
        meta = json.loads(CACHE_META.read_text())
        fetched_at = meta.get("fetched_at", 0)
        ttl = get_cache_ttl()
        return (time.time() - fetched_at) < ttl
    except Exception as e:
        log.warning("cache_check_failed", error=str(e))
        return False


def fetch_changelog(force_refresh: bool = False) -> str | None:
    """Fetch changelog from GitHub, using cache if valid."""
    # Check cache first
    if not force_refresh and is_cache_valid():
        log.debug("using_cached_changelog")
        return CACHE_FILE.read_text()

    # Fetch from GitHub
    log.info("fetching_changelog", url=CHANGELOG_URL)
    try:
        request = urllib.request.Request(
            CHANGELOG_URL,
            headers={"User-Agent": "Claude-Code-Changelog-Monitor/0.1.0"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            content = response.read().decode("utf-8")

        # Cache the result
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(content)
        CACHE_META.write_text(
            json.dumps(
                {
                    "fetched_at": time.time(),
                    "url": CHANGELOG_URL,
                    "size": len(content),
                }
            )
        )

        log.info("changelog_cached", size=len(content))
        return content

    except urllib.error.URLError as e:
        log.warning("fetch_failed", error=str(e))
        # Fall back to cache if available
        if CACHE_FILE.exists():
            log.info("using_stale_cache")
            return CACHE_FILE.read_text()
        return None

    except Exception as e:
        log.error("unexpected_fetch_error", error=str(e))
        return None


def get_last_known_version() -> str | None:
    """Get the last known version from roadmap."""
    roadmap_path = Path("/workspace/.claude/docs/ROADMAP.md")
    if not roadmap_path.exists():
        return None

    try:
        content = roadmap_path.read_text()
        # Look for "Last checked: X.Y.Z" pattern
        import re

        match = re.search(r"Last checked:\s*(\d+\.\d+\.\d+)", content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None
