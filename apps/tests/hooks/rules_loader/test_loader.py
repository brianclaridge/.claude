"""Tests for rules loader functionality."""

from pathlib import Path

import pytest

from claude_apps.hooks.rules_loader.loader import (
    filter_rules_for_reinforcement,
    load_rules,
    read_rule,
)


class TestLoadRules:
    """Tests for load_rules function."""

    def test_loads_markdown_files(self, tmp_path):
        """Test loads all .md files from directory."""
        # Create test rule files
        (tmp_path / "000-first.md").write_text("# Rule 000\nFirst rule")
        (tmp_path / "010-second.md").write_text("# Rule 010\nSecond rule")

        rules = load_rules(str(tmp_path))

        assert len(rules) == 2
        assert rules[0]["name"] == "000-first"
        assert rules[1]["name"] == "010-second"

    def test_returns_rules_in_sorted_order(self, tmp_path):
        """Test returns rules sorted by filename."""
        (tmp_path / "020-third.md").write_text("Third")
        (tmp_path / "000-first.md").write_text("First")
        (tmp_path / "010-second.md").write_text("Second")

        rules = load_rules(str(tmp_path))

        assert [r["name"] for r in rules] == ["000-first", "010-second", "020-third"]

    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Test returns empty list for non-existent directory."""
        rules = load_rules(str(tmp_path / "nonexistent"))

        assert rules == []

    def test_returns_empty_for_non_directory(self, tmp_path):
        """Test returns empty list when path is not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")

        rules = load_rules(str(file_path))

        assert rules == []

    def test_ignores_non_markdown_files(self, tmp_path):
        """Test ignores non-.md files."""
        (tmp_path / "rule.md").write_text("# Rule")
        (tmp_path / "readme.txt").write_text("Readme")
        (tmp_path / "config.yml").write_text("config: value")

        rules = load_rules(str(tmp_path))

        assert len(rules) == 1
        assert rules[0]["filename"] == "rule.md"


class TestReadRule:
    """Tests for read_rule function."""

    def test_reads_rule_content(self, tmp_path):
        """Test reads file content."""
        rule_file = tmp_path / "000-test.md"
        rule_file.write_text("# Test Rule\n\nContent here")

        rule = read_rule(rule_file)

        assert rule["content"] == "# Test Rule\n\nContent here"

    def test_extracts_rule_name(self, tmp_path):
        """Test extracts name from filename."""
        rule_file = tmp_path / "010-my-rule.md"
        rule_file.write_text("Content")

        rule = read_rule(rule_file)

        assert rule["name"] == "010-my-rule"
        assert rule["filename"] == "010-my-rule.md"

    def test_strips_whitespace(self, tmp_path):
        """Test strips leading/trailing whitespace."""
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("\n\n  Content  \n\n")

        rule = read_rule(rule_file)

        assert rule["content"] == "Content"

    def test_returns_none_on_error(self, tmp_path):
        """Test returns None on read error."""
        # Create a directory instead of file
        rule_file = tmp_path / "not-a-file"
        rule_file.mkdir()

        rule = read_rule(rule_file)

        assert rule is None


class TestFilterRulesForReinforcement:
    """Tests for filter_rules_for_reinforcement function."""

    def test_returns_all_rules_for_session_start(self):
        """Test returns all rules for SessionStart event."""
        rules = [
            {"name": "rule-1", "content": "Rule 1"},
            {"name": "rule-2", "content": "Rule 2"},
        ]
        config = {"reinforcement_enabled": False}

        filtered = filter_rules_for_reinforcement(rules, config, "SessionStart")

        assert len(filtered) == 2

    def test_filters_by_global_setting(self):
        """Test filters by global reinforcement_enabled."""
        rules = [
            {"name": "rule-1", "content": "Rule 1"},
            {"name": "rule-2", "content": "Rule 2"},
        ]
        config = {"reinforcement_enabled": True}

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 2

    def test_returns_empty_when_global_disabled(self):
        """Test returns empty when global disabled and no per-rule settings."""
        rules = [
            {"name": "rule-1", "content": "Rule 1"},
            {"name": "rule-2", "content": "Rule 2"},
        ]
        config = {"reinforcement_enabled": False}

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 0

    def test_per_rule_overrides_global(self):
        """Test per-rule setting overrides global."""
        rules = [
            {"name": "rule-1", "content": "Rule 1"},
            {"name": "rule-2", "content": "Rule 2"},
            {"name": "rule-3", "content": "Rule 3"},
        ]
        config = {
            "reinforcement_enabled": False,  # Global off
            "rules": {
                "rule-1": {"reinforce": True},  # Override to on
                "rule-3": {"reinforce": True},  # Override to on
            },
        }

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 2
        assert filtered[0]["name"] == "rule-1"
        assert filtered[1]["name"] == "rule-3"

    def test_per_rule_can_disable(self):
        """Test per-rule can disable when global enabled."""
        rules = [
            {"name": "rule-1", "content": "Rule 1"},
            {"name": "rule-2", "content": "Rule 2"},
        ]
        config = {
            "reinforcement_enabled": True,  # Global on
            "rules": {
                "rule-2": {"reinforce": False},  # Override to off
            },
        }

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 1
        assert filtered[0]["name"] == "rule-1"

    def test_handles_empty_rules_config(self):
        """Test handles empty per-rule config."""
        rules = [{"name": "rule-1", "content": "Content"}]
        config = {
            "reinforcement_enabled": True,
            # No "rules" key
        }

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 1

    def test_handles_missing_rule_name(self):
        """Test handles rule without name."""
        rules = [{"content": "Content only"}]  # No name
        config = {"reinforcement_enabled": True}

        filtered = filter_rules_for_reinforcement(rules, config, "UserPromptSubmit")

        assert len(filtered) == 1
