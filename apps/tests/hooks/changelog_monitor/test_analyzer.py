"""Tests for changelog analyzer."""

import pytest

from claude_apps.hooks.changelog_monitor.analyzer import (
    AnalysisResult,
    analyze_versions,
    format_context_injection,
    generate_roadmap_content,
)
from claude_apps.hooks.changelog_monitor.parser import VersionEntry


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = AnalysisResult()

        assert result.new_versions == []
        assert result.hook_opportunities == []
        assert result.skill_opportunities == []
        assert result.breaking_changes == []
        assert result.notable_features == []


class TestAnalyzeVersions:
    """Tests for analyze_versions function."""

    def test_identifies_hook_opportunities(self):
        """Test identifies hook-related features."""
        versions = [
            VersionEntry(
                version="1.0.0",
                features=["Added new hook event for file changes"],
            )
        ]

        result = analyze_versions(versions)

        assert len(result.hook_opportunities) == 1
        assert "hook" in result.hook_opportunities[0].lower()

    def test_identifies_skill_opportunities(self):
        """Test identifies skill/tool-related features."""
        versions = [
            VersionEntry(
                version="1.0.0",
                features=["New MCP tool integration"],
            )
        ]

        result = analyze_versions(versions)

        assert len(result.skill_opportunities) == 1

    def test_collects_breaking_changes(self):
        """Test collects breaking changes."""
        versions = [
            VersionEntry(
                version="2.0.0",
                breaking=["Removed deprecated API", "Changed hook format"],
            )
        ]

        result = analyze_versions(versions)

        assert len(result.breaking_changes) == 2

    def test_collects_all_features_as_notable(self):
        """Test all features are notable."""
        versions = [
            VersionEntry(
                version="1.0.0",
                features=["Feature 1", "Feature 2", "Feature 3"],
            )
        ]

        result = analyze_versions(versions)

        assert len(result.notable_features) == 3

    def test_includes_version_in_opportunities(self):
        """Test includes version number in opportunities."""
        versions = [
            VersionEntry(
                version="1.5.0",
                features=["New hook event"],
            )
        ]

        result = analyze_versions(versions)

        assert "[1.5.0]" in result.hook_opportunities[0]

    def test_handles_empty_versions(self):
        """Test handles empty version list."""
        result = analyze_versions([])

        assert result.new_versions == []


class TestFormatContextInjection:
    """Tests for format_context_injection function."""

    def test_includes_header(self):
        """Test includes header."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
        )

        formatted = format_context_injection(result)

        assert "## Claude Code Updates Available" in formatted

    def test_includes_latest_version(self):
        """Test includes latest version info."""
        result = AnalysisResult(
            new_versions=[
                VersionEntry(version="2.0.0", date="2025-01-15"),
                VersionEntry(version="1.0.0"),
            ],
        )

        formatted = format_context_injection(result)

        assert "2.0.0" in formatted
        assert "2025-01-15" in formatted

    def test_includes_breaking_changes(self):
        """Test includes breaking changes section."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
            breaking_changes=["API removed"],
        )

        formatted = format_context_injection(result)

        assert "Breaking Changes" in formatted
        assert "API removed" in formatted

    def test_includes_hook_opportunities(self):
        """Test includes hook opportunities section."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
            hook_opportunities=["New hook event"],
        )

        formatted = format_context_injection(result)

        assert "Hook Opportunities" in formatted

    def test_includes_skill_opportunities(self):
        """Test includes skill opportunities section."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
            skill_opportunities=["New tool support"],
        )

        formatted = format_context_injection(result)

        assert "Skill Opportunities" in formatted

    def test_returns_empty_for_no_versions(self):
        """Test returns empty for no versions."""
        result = AnalysisResult()

        formatted = format_context_injection(result)

        assert formatted == ""

    def test_truncates_long_lists(self):
        """Test truncates lists to 3 items."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
            breaking_changes=["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
        )

        formatted = format_context_injection(result)

        assert "Item 1" in formatted
        assert "Item 3" in formatted
        # Should only show first 3 items (not Item 4 or 5)
        assert "Item 4" not in formatted
        assert "Item 5" not in formatted

    def test_includes_roadmap_instruction(self):
        """Test includes roadmap instruction."""
        result = AnalysisResult(
            new_versions=[VersionEntry(version="1.0.0")],
        )

        formatted = format_context_injection(result)

        assert "/roadmap" in formatted


class TestGenerateRoadmapContent:
    """Tests for generate_roadmap_content function."""

    def test_includes_header(self):
        """Test includes markdown header."""
        result = AnalysisResult()

        content = generate_roadmap_content(result, None)

        assert "# Claude Code Feature Roadmap" in content

    def test_includes_features_section(self):
        """Test includes new features section."""
        result = AnalysisResult(
            notable_features=["Feature to evaluate"],
        )

        content = generate_roadmap_content(result, None)

        assert "## New Features to Evaluate" in content
        assert "Feature to evaluate" in content

    def test_includes_hook_section(self):
        """Test includes hook opportunities section."""
        result = AnalysisResult(
            hook_opportunities=["Hook opportunity"],
        )

        content = generate_roadmap_content(result, None)

        assert "## Hook Opportunities" in content

    def test_includes_skill_section(self):
        """Test includes skill opportunities section."""
        result = AnalysisResult(
            skill_opportunities=["Skill opportunity"],
        )

        content = generate_roadmap_content(result, None)

        assert "## Skill Opportunities" in content

    def test_includes_breaking_section(self):
        """Test includes breaking changes section."""
        result = AnalysisResult(
            breaking_changes=["Breaking change"],
        )

        content = generate_roadmap_content(result, None)

        assert "## Breaking Changes" in content

    def test_includes_version_history(self):
        """Test includes version history."""
        result = AnalysisResult(
            new_versions=[
                VersionEntry(version="1.0.0", date="2025-01-15", features=["Feature"]),
            ],
        )

        content = generate_roadmap_content(result, None)

        assert "## Version History" in content
        assert "### 1.0.0" in content

    def test_uses_todo_checkboxes(self):
        """Test uses markdown todo checkboxes."""
        result = AnalysisResult(
            notable_features=["Feature to evaluate"],
        )

        content = generate_roadmap_content(result, None)

        assert "- [ ]" in content
