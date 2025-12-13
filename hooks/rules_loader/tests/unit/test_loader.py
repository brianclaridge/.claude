"""Unit tests for loader.py - rule loading and filtering logic."""
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from loader import load_rules, read_rule, filter_rules_for_reinforcement


class TestLoadRules:
    """Tests for load_rules function."""

    def test_load_rules_returns_all_md_files(self, sample_rules_dir: Path) -> None:
        """Verify all .md files are loaded from directory."""
        rules = load_rules(str(sample_rules_dir))
        assert len(rules) == 3

    def test_load_rules_alphabetical_order(self, sample_rules_dir: Path) -> None:
        """Verify rules are loaded in alphabetical order."""
        rules = load_rules(str(sample_rules_dir))
        names = [r["name"] for r in rules]
        assert names == ["000-first-rule", "010-second-rule", "020-third-rule"]

    def test_load_rules_empty_directory(self, empty_rules_dir: Path) -> None:
        """Verify empty list returned for empty directory."""
        rules = load_rules(str(empty_rules_dir))
        assert rules == []

    def test_load_rules_nonexistent_directory(self, nonexistent_rules_dir: Path) -> None:
        """Verify empty list returned for nonexistent directory."""
        rules = load_rules(str(nonexistent_rules_dir))
        assert rules == []

    def test_load_rules_ignores_non_md_files(self, tmp_path: Path) -> None:
        """Verify non-.md files are ignored."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "rule.md").write_text("# Valid rule")
        (rules_dir / "readme.txt").write_text("Not a rule")
        (rules_dir / "config.json").write_text("{}")

        rules = load_rules(str(rules_dir))
        assert len(rules) == 1
        assert rules[0]["name"] == "rule"

    def test_load_rules_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Verify empty list when path is a file, not directory."""
        file_path = tmp_path / "not_a_dir.md"
        file_path.write_text("content")

        rules = load_rules(str(file_path))
        assert rules == []


class TestReadRule:
    """Tests for read_rule function."""

    def test_read_rule_returns_dict_structure(self, tmp_path: Path) -> None:
        """Verify returned dict has correct keys."""
        rule_file = tmp_path / "test-rule.md"
        rule_file.write_text("# Test content")

        result = read_rule(rule_file)

        assert result is not None
        assert "filename" in result
        assert "name" in result
        assert "content" in result

    def test_read_rule_extracts_stem_as_name(self, tmp_path: Path) -> None:
        """Verify name is filename without .md extension."""
        rule_file = tmp_path / "000-my-rule.md"
        rule_file.write_text("content")

        result = read_rule(rule_file)
        assert result is not None
        assert result["name"] == "000-my-rule"
        assert result["filename"] == "000-my-rule.md"

    def test_read_rule_strips_whitespace(self, tmp_path: Path) -> None:
        """Verify content is stripped of leading/trailing whitespace."""
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("  \n\n  Content here  \n\n  ")

        result = read_rule(rule_file)
        assert result is not None
        assert result["content"] == "Content here"

    def test_read_rule_preserves_utf8(self, tmp_path: Path) -> None:
        """Verify UTF-8 characters are preserved."""
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("Unicode: \u2713 \u2717 \u00e9")

        result = read_rule(rule_file)
        assert result is not None
        assert "\u2713" in result["content"]

    def test_read_rule_nonexistent_file(self, tmp_path: Path) -> None:
        """Verify None returned for nonexistent file."""
        result = read_rule(tmp_path / "missing.md")
        assert result is None


class TestFilterRulesForReinforcement:
    """Tests for filter_rules_for_reinforcement function."""

    # SessionStart tests - should always return all rules
    def test_session_start_returns_all_rules(
        self, sample_rules: list, config_reinforce_none: dict
    ) -> None:
        """SessionStart event returns ALL rules regardless of config."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_none, "SessionStart"
        )
        assert len(result) == 3

    def test_session_start_ignores_reinforcement_setting(
        self, sample_rules: list, config_reinforce_selective: dict
    ) -> None:
        """SessionStart ignores per-rule reinforcement settings."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_selective, "SessionStart"
        )
        assert len(result) == 3

    # UserPromptSubmit with global reinforcement enabled
    def test_user_prompt_global_reinforce_true(
        self, sample_rules: list, config_reinforce_all: dict
    ) -> None:
        """UserPromptSubmit with global reinforcement returns all rules."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_all, "UserPromptSubmit"
        )
        assert len(result) == 3

    # UserPromptSubmit with global reinforcement disabled
    def test_user_prompt_global_reinforce_false_no_overrides(
        self, sample_rules: list, config_reinforce_none: dict
    ) -> None:
        """UserPromptSubmit with no reinforcement returns empty list."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_none, "UserPromptSubmit"
        )
        assert len(result) == 0

    # UserPromptSubmit with selective reinforcement
    def test_user_prompt_selective_reinforcement(
        self, sample_rules: list, config_reinforce_selective: dict
    ) -> None:
        """UserPromptSubmit returns only rules with reinforce: true."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_selective, "UserPromptSubmit"
        )

        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "000-first-rule" in names
        assert "020-third-rule" in names
        assert "010-second-rule" not in names

    # Edge cases
    def test_empty_rules_list(self, config_reinforce_all: dict) -> None:
        """Empty rules list returns empty result."""
        result = filter_rules_for_reinforcement([], config_reinforce_all, "SessionStart")
        assert result == []

    def test_empty_config(self, sample_rules: list) -> None:
        """Empty config defaults to no reinforcement."""
        result = filter_rules_for_reinforcement(sample_rules, {}, "UserPromptSubmit")
        assert len(result) == 0

    def test_missing_rules_loader_key(self, sample_rules: list) -> None:
        """Config without rules_loader key defaults to no reinforcement."""
        config = {"other_key": "value"}
        result = filter_rules_for_reinforcement(sample_rules, config, "UserPromptSubmit")
        assert len(result) == 0

    def test_unknown_event_name_applies_filtering(
        self, sample_rules: list, config_reinforce_selective: dict
    ) -> None:
        """Unknown event names are treated like UserPromptSubmit (apply filtering)."""
        result = filter_rules_for_reinforcement(
            sample_rules, config_reinforce_selective, "UnknownEvent"
        )
        # Should apply filtering logic, not return all
        assert len(result) == 2
