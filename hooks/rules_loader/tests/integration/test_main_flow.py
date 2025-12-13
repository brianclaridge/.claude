"""Integration tests for complete hook execution flow.

Tests the integration of loader, formatter, and filtering logic together
without importing __main__ (which has relative import issues in test context).
"""
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from loader import load_rules, filter_rules_for_reinforcement
from formatter import format_to_hook_json


class TestEndToEndFlow:
    """End-to-end integration tests for the hook workflow."""

    @pytest.fixture
    def complete_test_environment(self, tmp_path: Path) -> dict[str, Any]:
        """Set up complete test environment with rules and configs."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        (rules_dir / "000-first.md").write_text("# First Rule\nContent one.")
        (rules_dir / "010-second.md").write_text("# Second Rule\nContent two.")

        global_config = {
            "rules_loader": {
                "reinforcement_enabled": False,
                "rules": {"000-first": {"reinforce": True}},
            }
        }

        return {
            "tmp_path": tmp_path,
            "rules_dir": rules_dir,
            "global_config": global_config,
        }

    def test_session_start_loads_all_rules(
        self, complete_test_environment: dict
    ) -> None:
        """Verify SessionStart workflow loads all rules."""
        env = complete_test_environment

        # Simulate the main workflow
        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config"], "SessionStart"
        )
        output = format_to_hook_json(rules, "SessionStart")

        parsed = json.loads(output)

        assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert "First Rule" in parsed["hookSpecificOutput"]["additionalContext"]
        assert "Second Rule" in parsed["hookSpecificOutput"]["additionalContext"]

    def test_user_prompt_filters_rules(
        self, complete_test_environment: dict
    ) -> None:
        """Verify UserPromptSubmit filters to reinforced rules only."""
        env = complete_test_environment

        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config"], "UserPromptSubmit"
        )
        output = format_to_hook_json(rules, "UserPromptSubmit")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert "First Rule" in context  # 000-first has reinforce: true
        assert "Second Rule" not in context  # 010-second not in config

    def test_output_is_valid_hook_json(
        self, complete_test_environment: dict
    ) -> None:
        """Verify output conforms to Claude Code hook JSON schema."""
        env = complete_test_environment

        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config"], "SessionStart"
        )
        output = format_to_hook_json(rules, "SessionStart")

        parsed = json.loads(output)

        # Verify schema compliance
        assert "hookSpecificOutput" in parsed
        assert isinstance(parsed["hookSpecificOutput"], dict)
        assert "hookEventName" in parsed["hookSpecificOutput"]
        assert "additionalContext" in parsed["hookSpecificOutput"]
        assert isinstance(parsed["hookSpecificOutput"]["additionalContext"], str)

    def test_handles_empty_rules_directory(self, tmp_path: Path) -> None:
        """Verify graceful handling of empty rules directory."""
        empty_rules = tmp_path / "empty_rules"
        empty_rules.mkdir()

        all_rules = load_rules(str(empty_rules))
        rules = filter_rules_for_reinforcement(all_rules, {}, "SessionStart")
        output = format_to_hook_json(rules, "SessionStart")

        parsed = json.loads(output)

        # Should produce valid but empty output
        assert parsed["hookSpecificOutput"]["additionalContext"] == ""


class TestFilteringLogic:
    """Tests specifically for the filtering logic in integration context."""

    @pytest.fixture
    def three_rule_environment(self, tmp_path: Path) -> dict[str, Any]:
        """Create environment with three rules for filtering tests."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        (rules_dir / "000-critical.md").write_text("# Critical Rule\nMust always load.")
        (rules_dir / "010-optional.md").write_text("# Optional Rule\nSometimes load.")
        (rules_dir / "020-another.md").write_text("# Another Rule\nAnother optional.")

        return {
            "rules_dir": rules_dir,
            "global_config_selective": {
                "rules_loader": {
                    "reinforcement_enabled": False,
                    "rules": {
                        "000-critical": {"reinforce": True},
                        "020-another": {"reinforce": True},
                    },
                }
            },
            "global_config_all": {
                "rules_loader": {
                    "reinforcement_enabled": True,
                    "rules": {},
                }
            },
            "global_config_none": {
                "rules_loader": {
                    "reinforcement_enabled": False,
                    "rules": {},
                }
            },
        }

    def test_selective_reinforcement_two_of_three(
        self, three_rule_environment: dict
    ) -> None:
        """Verify selective reinforcement returns exactly configured rules."""
        env = three_rule_environment

        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config_selective"], "UserPromptSubmit"
        )
        output = format_to_hook_json(rules, "UserPromptSubmit")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert "Critical Rule" in context
        assert "Another Rule" in context
        assert "Optional Rule" not in context

    def test_global_reinforcement_all(
        self, three_rule_environment: dict
    ) -> None:
        """Verify global reinforcement=true returns all rules."""
        env = three_rule_environment

        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config_all"], "UserPromptSubmit"
        )
        output = format_to_hook_json(rules, "UserPromptSubmit")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert "Critical Rule" in context
        assert "Optional Rule" in context
        assert "Another Rule" in context

    def test_no_reinforcement_empty_context(
        self, three_rule_environment: dict
    ) -> None:
        """Verify no reinforcement returns empty context."""
        env = three_rule_environment

        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config_none"], "UserPromptSubmit"
        )
        output = format_to_hook_json(rules, "UserPromptSubmit")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert context == ""

    def test_session_start_always_returns_all(
        self, three_rule_environment: dict
    ) -> None:
        """Verify SessionStart always returns all rules regardless of config."""
        env = three_rule_environment

        # Even with no reinforcement config, SessionStart returns all
        all_rules = load_rules(str(env["rules_dir"]))
        rules = filter_rules_for_reinforcement(
            all_rules, env["global_config_none"], "SessionStart"
        )
        output = format_to_hook_json(rules, "SessionStart")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert "Critical Rule" in context
        assert "Optional Rule" in context
        assert "Another Rule" in context


class TestCompleteWorkflow:
    """Tests for the complete workflow from rules to JSON output."""

    def test_alphabetical_ordering_preserved(self, tmp_path: Path) -> None:
        """Verify rules maintain alphabetical order through workflow."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        # Create rules in non-alphabetical order
        (rules_dir / "020-z-rule.md").write_text("# Z Rule")
        (rules_dir / "000-a-rule.md").write_text("# A Rule")
        (rules_dir / "010-m-rule.md").write_text("# M Rule")

        all_rules = load_rules(str(rules_dir))
        output = format_to_hook_json(all_rules, "SessionStart")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        # A should come before M, M before Z
        a_pos = context.find("A Rule")
        m_pos = context.find("M Rule")
        z_pos = context.find("Z Rule")

        assert a_pos < m_pos < z_pos

    def test_unicode_preserved_through_workflow(self, tmp_path: Path) -> None:
        """Verify Unicode characters are preserved through entire workflow."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        (rules_dir / "000-unicode.md").write_text("Check: ✓ ✗ é ñ 中文")

        all_rules = load_rules(str(rules_dir))
        output = format_to_hook_json(all_rules, "SessionStart")

        # Unicode should be present in output, not escaped
        assert "✓" in output
        assert "✗" in output
        assert "中文" in output
        assert "\\u" not in output  # Not escaped

    def test_multiline_content_preserved(self, tmp_path: Path) -> None:
        """Verify multiline rule content is preserved."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        multiline_content = """# Rule Header

First paragraph with important info.

## Section

- Bullet one
- Bullet two

Code example:
```python
print("hello")
```"""
        (rules_dir / "000-multiline.md").write_text(multiline_content)

        all_rules = load_rules(str(rules_dir))
        output = format_to_hook_json(all_rules, "SessionStart")

        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        assert "First paragraph" in context
        assert "Bullet one" in context
        assert 'print("hello")' in context
