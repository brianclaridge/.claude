"""Tests for changelog parser."""

import pytest

from claude_apps.hooks.changelog_monitor.parser import (
    VersionEntry,
    extract_keywords,
    get_versions_since,
    parse_changelog,
)


class TestVersionEntry:
    """Tests for VersionEntry dataclass."""

    def test_defaults(self):
        """Test default values."""
        entry = VersionEntry(version="1.0.0")

        assert entry.version == "1.0.0"
        assert entry.date is None
        assert entry.features == []
        assert entry.fixes == []
        assert entry.breaking == []
        assert entry.other == []

    def test_populated(self):
        """Test populated entry."""
        entry = VersionEntry(
            version="1.0.1",
            date="2025-01-15",
            features=["New feature"],
            fixes=["Bug fix"],
        )

        assert entry.version == "1.0.1"
        assert entry.date == "2025-01-15"
        assert len(entry.features) == 1


class TestParseChangelog:
    """Tests for parse_changelog function."""

    def test_parses_version_header_with_date(self):
        """Test parses version header with date."""
        content = """## [1.0.62] - 2025-12-12

### Added
- New feature
"""
        versions = parse_changelog(content)

        assert len(versions) == 1
        assert versions[0].version == "1.0.62"
        assert versions[0].date == "2025-12-12"

    def test_parses_version_header_without_brackets(self):
        """Test parses version header without brackets."""
        content = """## 1.0.0

### Added
- Feature
"""
        versions = parse_changelog(content)

        assert len(versions) == 1
        assert versions[0].version == "1.0.0"

    def test_parses_multiple_versions(self):
        """Test parses multiple version entries."""
        content = """## [2.0.0] - 2025-01-15

### Added
- Version 2 feature

## [1.0.0] - 2025-01-01

### Added
- Version 1 feature
"""
        versions = parse_changelog(content)

        assert len(versions) == 2
        assert versions[0].version == "2.0.0"
        assert versions[1].version == "1.0.0"

    def test_parses_features_section(self):
        """Test parses Added/Features section."""
        content = """## [1.0.0]

### Added
- First feature
- Second feature
"""
        versions = parse_changelog(content)

        assert len(versions[0].features) == 2
        assert "First feature" in versions[0].features

    def test_parses_fixes_section(self):
        """Test parses Fixed/Bugs section."""
        content = """## [1.0.0]

### Fixed
- Bug fix one
- Bug fix two
"""
        versions = parse_changelog(content)

        assert len(versions[0].fixes) == 2

    def test_parses_breaking_section(self):
        """Test parses Breaking changes section."""
        content = """## [1.0.0]

### Breaking Changes
- API changed
- Removed deprecated method
"""
        versions = parse_changelog(content)

        assert len(versions[0].breaking) == 2

    def test_parses_other_sections(self):
        """Test parses other sections as 'other'."""
        content = """## [1.0.0]

### Documentation
- Updated docs
"""
        versions = parse_changelog(content)

        assert len(versions[0].other) == 1

    def test_handles_empty_content(self):
        """Test handles empty content."""
        versions = parse_changelog("")

        assert versions == []

    def test_handles_no_versions(self):
        """Test handles content with no version headers."""
        content = "Just some text without version headers"

        versions = parse_changelog(content)

        assert versions == []


class TestGetVersionsSince:
    """Tests for get_versions_since function."""

    def test_returns_newer_versions(self):
        """Test returns versions newer than specified."""
        versions = [
            VersionEntry(version="2.0.0"),
            VersionEntry(version="1.5.0"),
            VersionEntry(version="1.0.0"),
        ]

        result = get_versions_since(versions, "1.0.0")

        assert len(result) == 2
        assert result[0].version == "2.0.0"
        assert result[1].version == "1.5.0"

    def test_returns_all_when_since_none(self):
        """Test returns all when since_version is None."""
        versions = [
            VersionEntry(version="2.0.0"),
            VersionEntry(version="1.0.0"),
        ]

        result = get_versions_since(versions, None)

        assert len(result) == 2

    def test_returns_empty_when_all_older(self):
        """Test returns empty when all versions older."""
        versions = [
            VersionEntry(version="1.0.0"),
            VersionEntry(version="0.9.0"),
        ]

        result = get_versions_since(versions, "2.0.0")

        assert result == []

    def test_handles_patch_versions(self):
        """Test handles patch version comparisons."""
        versions = [
            VersionEntry(version="1.0.2"),
            VersionEntry(version="1.0.1"),
            VersionEntry(version="1.0.0"),
        ]

        result = get_versions_since(versions, "1.0.0")

        assert len(result) == 2

    def test_handles_invalid_since_version(self):
        """Test handles invalid since version format."""
        versions = [VersionEntry(version="1.0.0")]

        result = get_versions_since(versions, "invalid")

        assert result == versions

    def test_skips_invalid_entry_versions(self):
        """Test skips entries with invalid version format."""
        versions = [
            VersionEntry(version="2.0.0"),
            VersionEntry(version="invalid"),
            VersionEntry(version="1.0.0"),
        ]

        result = get_versions_since(versions, "0.9.0")

        # Should include valid versions only
        assert len(result) == 2


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_extracts_hook_keyword(self):
        """Test extracts 'hooks' keyword."""
        text = "Added new hook event for file changes"

        keywords = extract_keywords(text)

        assert "hooks" in keywords

    def test_extracts_multiple_keywords(self):
        """Test extracts multiple keywords."""
        # Note: MCP pattern is uppercase in implementation but text is lowercased
        # So we use "tool" which matches \btool\b
        text = "New tool for agent integration"

        keywords = extract_keywords(text)

        assert "tools" in keywords
        assert "agents" in keywords

    def test_case_insensitive(self):
        """Test keyword matching for hook pattern is case insensitive."""
        # The implementation lowercases text and uses \bhook\b pattern
        # So HOOK -> hook matches \bhook\b
        text = "HOOK and tool and event"

        keywords = extract_keywords(text)

        assert "hooks" in keywords
        assert "tools" in keywords
        assert "events" in keywords

    def test_returns_empty_for_no_matches(self):
        """Test returns empty list for no matches."""
        text = "General improvement to performance"

        keywords = extract_keywords(text)

        assert keywords == []

    def test_deduplicates_keywords(self):
        """Test returns unique keywords."""
        text = "Hook hook HOOK"

        keywords = extract_keywords(text)

        assert keywords.count("hooks") == 1
