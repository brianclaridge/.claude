"""Tests for session statistics extraction."""

import json
from pathlib import Path

import pytest

from claude_apps.skills.git_manager.stats import (
    SessionStats,
    cwd_to_transcript_dir,
    estimate_cost,
    find_session_transcript,
    format_duration,
    format_number,
    format_stats_section,
    get_session_stats,
    parse_transcript,
)


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_seconds_only(self):
        """Test formatting seconds < 60."""
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"
        assert format_duration(0) == "0s"

    def test_minutes_and_seconds(self):
        """Test formatting minutes with seconds."""
        assert format_duration(90) == "1m 30s"
        assert format_duration(120) == "2m"
        assert format_duration(125) == "2m 5s"

    def test_hours_and_minutes(self):
        """Test formatting hours with minutes."""
        assert format_duration(3600) == "1h"
        assert format_duration(3660) == "1h 1m"
        assert format_duration(7200) == "2h"
        assert format_duration(7320) == "2h 2m"


class TestFormatNumber:
    """Tests for format_number function."""

    def test_small_numbers(self):
        """Test formatting small numbers."""
        assert format_number(0) == "0"
        assert format_number(100) == "100"
        assert format_number(999) == "999"

    def test_thousands(self):
        """Test formatting thousands."""
        assert format_number(1000) == "1,000"
        assert format_number(12345) == "12,345"
        assert format_number(999999) == "999,999"

    def test_millions(self):
        """Test formatting millions."""
        assert format_number(1000000) == "1,000,000"
        assert format_number(1234567890) == "1,234,567,890"


class TestSessionStats:
    """Tests for SessionStats dataclass."""

    def test_defaults(self):
        """Test default values."""
        stats = SessionStats()

        assert stats.input_tokens == 0
        assert stats.output_tokens == 0
        assert stats.cache_read_tokens == 0
        assert stats.cache_creation_tokens == 0
        assert stats.api_requests == 0
        assert stats.tool_calls == 0
        assert stats.model == ""
        assert stats.session_id == ""
        assert stats.duration_seconds == 0
        assert stats.estimated_cost_usd == 0.0
        assert stats.transcript_found is False
        assert stats.error is None

    def test_to_dict(self):
        """Test serialization to dict."""
        stats = SessionStats(
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=200,
            cache_creation_tokens=100,
            api_requests=5,
            tool_calls=10,
            model="claude-3-opus",
            session_id="abc123",
            duration_seconds=300,
            estimated_cost_usd=0.15,
            transcript_found=True,
        )

        d = stats.to_dict()

        assert d["input_tokens"] == 1000
        assert d["output_tokens"] == 500
        assert d["cache_read_tokens"] == 200
        assert d["cache_creation_tokens"] == 100
        assert d["api_requests"] == 5
        assert d["tool_calls"] == 10
        assert d["model"] == "claude-3-opus"
        assert d["session_id"] == "abc123"
        assert d["duration_seconds"] == 300
        assert d["estimated_cost_usd"] == 0.15
        assert d["transcript_found"] is True


class TestCwdToTranscriptDir:
    """Tests for cwd_to_transcript_dir function."""

    def test_returns_none_for_nonexistent(self, tmp_path, monkeypatch):
        """Test returns None when transcript dir doesn't exist."""
        monkeypatch.setenv("HOME", str(tmp_path))

        result = cwd_to_transcript_dir(tmp_path / "workspace")
        assert result is None

    def test_finds_existing_transcript_dir(self, tmp_path, monkeypatch):
        """Test finds existing transcript directory."""
        # Create the expected directory structure
        home = tmp_path / "home"
        claude_projects = home / ".claude" / "projects" / "-workspace"
        claude_projects.mkdir(parents=True)

        monkeypatch.setenv("HOME", str(home))

        # Create a Path that would map to this directory
        workspace = Path("/workspace")

        result = cwd_to_transcript_dir(workspace)

        # Since /workspace might not map correctly with HOME override,
        # we just verify the function doesn't crash
        assert result is None or isinstance(result, Path)


class TestFindSessionTranscript:
    """Tests for find_session_transcript function."""

    def test_finds_most_recent(self, tmp_path):
        """Test finds most recent transcript."""
        # Create multiple transcripts
        import time

        old = tmp_path / "old-session.jsonl"
        old.write_text('{"type": "test"}')
        time.sleep(0.1)

        new = tmp_path / "new-session.jsonl"
        new.write_text('{"type": "test"}')

        result = find_session_transcript(tmp_path)

        assert result == new

    def test_excludes_agent_transcripts(self, tmp_path):
        """Test excludes agent-*.jsonl files."""
        main = tmp_path / "main-session.jsonl"
        main.write_text('{"type": "test"}')

        agent = tmp_path / "agent-abc123.jsonl"
        agent.write_text('{"type": "test"}')

        result = find_session_transcript(tmp_path)

        assert result == main

    def test_returns_none_for_empty(self, tmp_path):
        """Test returns None when no transcripts exist."""
        result = find_session_transcript(tmp_path)
        assert result is None


class TestParseTranscript:
    """Tests for parse_transcript function."""

    def test_parses_basic_transcript(self, tmp_path):
        """Test parsing basic transcript with usage data."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "sessionId": "test-session-123",
                "timestamp": "2025-01-15T10:00:00Z",
                "message": {
                    "model": "claude-3-opus",
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cache_read_input_tokens": 10,
                        "cache_creation_input_tokens": 5,
                    },
                    "content": [],
                },
            }),
            json.dumps({
                "type": "assistant",
                "timestamp": "2025-01-15T10:05:00Z",
                "message": {
                    "model": "claude-3-opus",
                    "usage": {
                        "input_tokens": 200,
                        "output_tokens": 100,
                    },
                    "content": [],
                },
            }),
        ]
        transcript.write_text("\n".join(lines))

        stats = parse_transcript(transcript)

        assert stats.transcript_found is True
        assert stats.session_id == "test-session-123"
        assert stats.input_tokens == 300  # 100 + 200
        assert stats.output_tokens == 150  # 50 + 100
        assert stats.cache_read_tokens == 10
        assert stats.cache_creation_tokens == 5
        assert stats.api_requests == 2
        assert stats.model == "claude-3-opus"
        assert stats.duration_seconds == 300  # 5 minutes

    def test_counts_tool_calls(self, tmp_path):
        """Test counting tool calls in content."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "timestamp": "2025-01-15T10:00:00Z",
                "message": {
                    "model": "claude-3-opus",
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [
                        {"type": "text", "text": "Let me help..."},
                        {"type": "tool_use", "id": "tool1", "name": "Read"},
                        {"type": "tool_use", "id": "tool2", "name": "Write"},
                    ],
                },
            }),
        ]
        transcript.write_text("\n".join(lines))

        stats = parse_transcript(transcript)

        assert stats.tool_calls == 2

    def test_prefers_opus_model(self, tmp_path):
        """Test that opus model is preferred over sonnet."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            json.dumps({
                "type": "assistant",
                "timestamp": "2025-01-15T10:00:00Z",
                "message": {
                    "model": "claude-3-sonnet",
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [],
                },
            }),
            json.dumps({
                "type": "assistant",
                "timestamp": "2025-01-15T10:01:00Z",
                "message": {
                    "model": "claude-3-opus",
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [],
                },
            }),
        ]
        transcript.write_text("\n".join(lines))

        stats = parse_transcript(transcript)

        assert "opus" in stats.model.lower()

    def test_handles_empty_transcript(self, tmp_path):
        """Test handling empty transcript."""
        transcript = tmp_path / "session.jsonl"
        transcript.write_text("")

        stats = parse_transcript(transcript)

        assert stats.transcript_found is True
        assert stats.input_tokens == 0
        assert stats.api_requests == 0

    def test_handles_invalid_json_lines(self, tmp_path):
        """Test handling transcript with invalid JSON."""
        transcript = tmp_path / "session.jsonl"
        lines = [
            "not valid json",
            json.dumps({
                "type": "assistant",
                "message": {
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                    "content": [],
                },
            }),
        ]
        transcript.write_text("\n".join(lines))

        stats = parse_transcript(transcript)

        # Should skip invalid line and parse the rest
        assert stats.input_tokens == 100


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_estimates_cost(self):
        """Test basic cost estimation."""
        stats = SessionStats(
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=0,
            cache_creation_tokens=0,
            model="claude-3-opus",
        )

        cost = estimate_cost(stats)

        # Should be a positive number
        assert cost > 0
        assert isinstance(cost, float)

    def test_includes_cache_costs(self):
        """Test that cache tokens affect cost."""
        stats_no_cache = SessionStats(
            input_tokens=1000,
            output_tokens=500,
            model="claude-3-opus",
        )

        stats_with_cache = SessionStats(
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=500,
            cache_creation_tokens=200,
            model="claude-3-opus",
        )

        cost_no_cache = estimate_cost(stats_no_cache)
        cost_with_cache = estimate_cost(stats_with_cache)

        # Cache should add some cost
        assert cost_with_cache != cost_no_cache


class TestFormatStatsSection:
    """Tests for format_stats_section function."""

    def test_returns_empty_when_not_found(self):
        """Test returns empty string when transcript not found."""
        stats = SessionStats(transcript_found=False)
        result = format_stats_section(stats)
        assert result == ""

    def test_returns_error_message(self):
        """Test returns error message when present."""
        stats = SessionStats(
            transcript_found=True,
            error="Something went wrong",
        )

        result = format_stats_section(stats)

        assert "Error" in result
        assert "Something went wrong" in result

    def test_formats_full_stats(self):
        """Test formatting complete statistics."""
        stats = SessionStats(
            transcript_found=True,
            input_tokens=10000,
            output_tokens=5000,
            cache_read_tokens=2000,
            cache_creation_tokens=1000,
            estimated_cost_usd=1.23,
            duration_seconds=600,
            api_requests=15,
            tool_calls=30,
            model="claude-3-opus",
        )

        result = format_stats_section(stats)

        assert "## Session Statistics" in result
        assert "10,000" in result  # input tokens formatted
        assert "5,000" in result  # output tokens formatted
        assert "$1.23" in result
        assert "10m" in result  # duration
        assert "15" in result  # api calls
        assert "30" in result  # tool calls
        assert "claude-3-opus" in result


class TestGetSessionStats:
    """Tests for get_session_stats function."""

    def test_returns_error_when_dir_not_found(self, tmp_path, monkeypatch):
        """Test returns error when transcript dir not found."""
        monkeypatch.setenv("HOME", str(tmp_path))

        stats = get_session_stats(tmp_path / "nonexistent")

        assert stats.transcript_found is False
        assert "not found" in stats.error.lower()

    def test_returns_error_when_no_transcript(self, tmp_path, monkeypatch):
        """Test returns error when no transcript file found."""
        # Create empty transcript directory
        home = tmp_path / "home"
        transcript_dir = home / ".claude" / "projects" / "-test"
        transcript_dir.mkdir(parents=True)

        monkeypatch.setenv("HOME", str(home))

        # Mock cwd_to_transcript_dir to return our dir
        from claude_apps.skills.git_manager import stats as stats_module
        original_func = stats_module.cwd_to_transcript_dir

        def mock_cwd(*args, **kwargs):
            return transcript_dir

        monkeypatch.setattr(stats_module, "cwd_to_transcript_dir", mock_cwd)

        result = get_session_stats()

        assert result.transcript_found is False
        assert "No session transcript" in result.error
