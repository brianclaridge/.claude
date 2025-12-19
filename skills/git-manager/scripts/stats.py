"""Session statistics extraction from Claude Code transcripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from .pricing import get_cache_multipliers, get_model_rates

logger = structlog.get_logger()


@dataclass
class SessionStats:
    """Aggregated session statistics from transcript."""

    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    # Activity metrics
    api_requests: int = 0
    tool_calls: int = 0

    # Session metadata
    model: str = ""
    session_id: str = ""
    duration_seconds: int = 0

    # Derived
    estimated_cost_usd: float = 0.0

    # Status
    transcript_found: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "api_requests": self.api_requests,
            "tool_calls": self.tool_calls,
            "model": self.model,
            "session_id": self.session_id,
            "duration_seconds": self.duration_seconds,
            "estimated_cost_usd": self.estimated_cost_usd,
            "transcript_found": self.transcript_found,
            "error": self.error,
        }


def cwd_to_transcript_dir(cwd: Optional[Path] = None) -> Optional[Path]:
    """Convert CWD to transcript directory path.

    Claude Code stores transcripts in:
    ~/.claude/projects/-{cwd-with-slashes-as-dashes}/

    Example:
        /workspace/projects/personal/claude-stack
        -> ~/.claude/projects/-workspace-z-projects-personal-claude-stack/
    """
    if cwd is None:
        cwd = Path.cwd()

    # Convert path to directory name format
    # /workspace/z/projects/... -> -workspace-z-projects-...
    path_str = str(cwd)
    dirname = path_str.replace("/", "-")
    if not dirname.startswith("-"):
        dirname = "-" + dirname

    transcript_dir = Path.home() / ".claude" / "projects" / dirname

    if transcript_dir.exists():
        return transcript_dir

    logger.debug("transcript_dir_not_found", path=str(transcript_dir))
    return None


def find_session_transcript(transcript_dir: Path) -> Optional[Path]:
    """Find most recent main session transcript (exclude agent-*.jsonl)."""
    try:
        candidates = [
            f
            for f in transcript_dir.glob("*.jsonl")
            if not f.name.startswith("agent-")
        ]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
    except OSError as e:
        logger.error("transcript_search_failed", error=str(e))

    return None


def parse_transcript(transcript_path: Path) -> SessionStats:
    """Parse transcript JSONL and extract statistics."""
    stats = SessionStats(transcript_found=True)

    timestamps: list[datetime] = []
    models_seen: set[str] = set()

    try:
        with transcript_path.open("r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Extract session ID from first record that has it
                if not stats.session_id and "sessionId" in record:
                    stats.session_id = record["sessionId"]

                # Parse timestamps for duration calculation
                if "timestamp" in record:
                    try:
                        ts_str = record["timestamp"]
                        # Handle ISO format with Z suffix
                        ts_str = ts_str.replace("Z", "+00:00")
                        ts = datetime.fromisoformat(ts_str)
                        timestamps.append(ts)
                    except (ValueError, AttributeError):
                        pass

                # Process assistant messages with usage data
                if record.get("type") == "assistant":
                    message = record.get("message", {})
                    usage = message.get("usage", {})

                    if usage:
                        stats.api_requests += 1
                        stats.input_tokens += usage.get("input_tokens", 0)
                        stats.output_tokens += usage.get("output_tokens", 0)
                        stats.cache_read_tokens += usage.get(
                            "cache_read_input_tokens", 0
                        )
                        stats.cache_creation_tokens += usage.get(
                            "cache_creation_input_tokens", 0
                        )

                    # Track model (exclude synthetic)
                    model = message.get("model", "")
                    if model and model != "<synthetic>":
                        models_seen.add(model)

                    # Count tool calls in content
                    content = message.get("content", [])
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            stats.tool_calls += 1

        # Calculate duration from first to last timestamp
        if len(timestamps) >= 2:
            timestamps.sort()
            duration = timestamps[-1] - timestamps[0]
            stats.duration_seconds = int(duration.total_seconds())

        # Set primary model (prefer opus over sonnet, most recent if tie)
        if models_seen:
            # Sort to get consistent ordering, prefer opus
            sorted_models = sorted(models_seen)
            opus_models = [m for m in sorted_models if "opus" in m.lower()]
            stats.model = opus_models[-1] if opus_models else sorted_models[-1]

        # Estimate cost
        stats.estimated_cost_usd = estimate_cost(stats)

    except Exception as e:
        stats.error = str(e)
        logger.error("transcript_parse_failed", error=str(e))

    return stats


def estimate_cost(stats: SessionStats) -> float:
    """Estimate session cost based on token usage and model.

    Pricing loaded from config/pricing.yml with fallback to defaults.
    """
    input_rate, output_rate = get_model_rates(stats.model)
    cache_read_mult, cache_write_mult = get_cache_multipliers()

    # Calculate costs
    input_cost = stats.input_tokens * input_rate
    output_cost = stats.output_tokens * output_rate
    cache_read_cost = stats.cache_read_tokens * input_rate * cache_read_mult
    cache_write_cost = stats.cache_creation_tokens * input_rate * cache_write_mult

    return round(input_cost + output_cost + cache_read_cost + cache_write_cost, 4)


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    secs = seconds % 60

    if minutes < 60:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"

    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def format_number(n: int) -> str:
    """Format number with thousands separator."""
    return f"{n:,}"


def format_stats_section(stats: SessionStats) -> str:
    """Format statistics as markdown section for commit message."""
    if not stats.transcript_found:
        return ""

    if stats.error:
        return f"## Session Statistics\n\n_Error: {stats.error}_"

    lines = ["## Session Statistics", ""]

    # Token summary
    lines.append(
        f"- **Tokens**: {format_number(stats.input_tokens)} input / "
        f"{format_number(stats.output_tokens)} output"
    )

    # Cache stats (only if non-zero)
    if stats.cache_read_tokens or stats.cache_creation_tokens:
        lines.append(
            f"- **Cache**: {format_number(stats.cache_read_tokens)} read / "
            f"{format_number(stats.cache_creation_tokens)} created"
        )

    # Cost
    lines.append(f"- **Cost**: ${stats.estimated_cost_usd:.2f}")

    # Duration
    if stats.duration_seconds > 0:
        lines.append(f"- **Duration**: {format_duration(stats.duration_seconds)}")

    # Activity
    lines.append(f"- **API Calls**: {stats.api_requests}")
    lines.append(f"- **Tool Calls**: {stats.tool_calls}")

    # Model
    if stats.model:
        lines.append(f"- **Model**: {stats.model}")

    return "\n".join(lines)


def get_session_stats(cwd: Optional[Path] = None) -> SessionStats:
    """Main entry point: discover transcript and parse stats.

    Args:
        cwd: Working directory to derive transcript location from.
             Defaults to current working directory.

    Returns:
        SessionStats with parsed data or error information.
    """
    transcript_dir = cwd_to_transcript_dir(cwd)

    if not transcript_dir:
        stats = SessionStats()
        stats.error = "Transcript directory not found"
        return stats

    transcript_path = find_session_transcript(transcript_dir)

    if not transcript_path:
        stats = SessionStats()
        stats.error = "No session transcript found"
        return stats

    return parse_transcript(transcript_path)
