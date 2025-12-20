"""Tests for Taskfile validation rules based on Rule 090."""

import pytest

from claude_apps.skills.taskfile_manager.rules import (
    Severity,
    Violation,
    check_aliases,
    check_platform_specific,
    check_silent_mode,
    check_task_description,
    check_task_naming,
    check_template_whitespace,
    check_variable_uppercase,
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Test severity values."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestViolation:
    """Tests for Violation dataclass."""

    def test_creation(self):
        """Test creating a violation."""
        v = Violation(
            line=10,
            column=5,
            rule="test-rule",
            severity=Severity.ERROR,
            message="Test message",
            original="original",
            suggested="suggested",
        )

        assert v.line == 10
        assert v.column == 5
        assert v.rule == "test-rule"
        assert v.severity == Severity.ERROR
        assert v.message == "Test message"
        assert v.original == "original"
        assert v.suggested == "suggested"


class TestCheckVariableUppercase:
    """Tests for check_variable_uppercase rule."""

    def test_uppercase_variables_ok(self):
        """Test no violation for uppercase variables."""
        content = {"vars": {"BUILD_DIR": "./dist", "VERSION": "1.0.0"}}
        violations = check_variable_uppercase(content, 1, "")

        assert len(violations) == 0

    def test_lowercase_variable(self):
        """Test detects lowercase variable."""
        content = {"vars": {"build_dir": "./dist"}}
        violations = check_variable_uppercase(content, 1, "")

        assert len(violations) == 1
        assert violations[0].rule == "variable-uppercase"
        assert violations[0].severity == Severity.ERROR
        assert violations[0].suggested == "BUILD_DIR"

    def test_mixed_case_variable(self):
        """Test detects mixed case variable."""
        content = {"vars": {"BuildDir": "./dist"}}
        violations = check_variable_uppercase(content, 1, "")

        assert len(violations) == 1
        assert violations[0].suggested == "BUILDDIR"

    def test_multiple_variables(self):
        """Test checks multiple variables."""
        content = {"vars": {"OK": "1", "bad": "2", "GOOD": "3", "ugly": "4"}}
        violations = check_variable_uppercase(content, 1, "")

        assert len(violations) == 2

    def test_no_vars_section(self):
        """Test handles missing vars section."""
        content = {"tasks": {"build": {}}}
        violations = check_variable_uppercase(content, 1, "")

        assert len(violations) == 0


class TestCheckTemplateWhitespace:
    """Tests for check_template_whitespace rule."""

    def test_correct_template_syntax(self):
        """Test no violation for correct syntax."""
        violations = check_template_whitespace(1, "cmd: echo {{.BINARY_NAME}}")

        assert len(violations) == 0

    def test_whitespace_after_open(self):
        """Test detects whitespace after opening."""
        violations = check_template_whitespace(1, "cmd: echo {{ .VAR}}")

        assert len(violations) == 1
        assert violations[0].rule == "template-whitespace"
        assert "{{." in violations[0].suggested

    def test_whitespace_before_close(self):
        """Test detects whitespace immediately after dot before close."""
        # Pattern only matches whitespace between . and }}
        # e.g., {{. }} not {{.VAR }}
        violations = check_template_whitespace(1, "cmd: echo {{. }}")

        assert len(violations) == 1

    def test_whitespace_both(self):
        """Test detects whitespace on both sides with dot-adjacent pattern."""
        # Pattern matches {{ .X }} - fixes leading only unless trailing is after dot
        violations = check_template_whitespace(1, "cmd: echo {{ . }}")

        assert len(violations) == 1
        assert violations[0].suggested == "{{.}}"

    def test_multiple_templates(self):
        """Test checks multiple templates on same line."""
        violations = check_template_whitespace(1, "{{ .A }} and {{ .B }}")

        assert len(violations) == 2

    def test_no_templates(self):
        """Test handles lines without templates."""
        violations = check_template_whitespace(1, "cmd: echo hello")

        assert len(violations) == 0


class TestCheckTaskNaming:
    """Tests for check_task_naming rule."""

    def test_kebab_case_ok(self):
        """Test no violation for kebab-case."""
        violations = check_task_naming("build-app", 1)

        assert len(violations) == 0

    def test_namespaced_ok(self):
        """Test no violation for namespace:task."""
        violations = check_task_naming("docker:build", 1)

        assert len(violations) == 0

    def test_simple_name_ok(self):
        """Test no violation for simple lowercase."""
        violations = check_task_naming("build", 1)

        assert len(violations) == 0

    def test_camel_case(self):
        """Test detects camelCase."""
        violations = check_task_naming("buildApp", 1)

        assert len(violations) == 1
        assert violations[0].rule == "task-kebab-case"
        assert violations[0].suggested == "buildapp"

    def test_snake_case(self):
        """Test detects snake_case."""
        violations = check_task_naming("build_app", 1)

        assert len(violations) == 1
        assert violations[0].suggested == "build-app"

    def test_pascal_case(self):
        """Test detects PascalCase."""
        violations = check_task_naming("BuildApp", 1)

        assert len(violations) == 1

    def test_private_task_underscore_ok(self):
        """Test allows leading underscore for private tasks."""
        violations = check_task_naming("_internal", 1)

        assert len(violations) == 0


class TestCheckTaskDescription:
    """Tests for check_task_description rule."""

    def test_with_desc_ok(self):
        """Test no violation when desc present."""
        violations = check_task_description("build", {"desc": "Build app"}, 1)

        assert len(violations) == 0

    def test_missing_desc(self):
        """Test detects missing desc."""
        violations = check_task_description("build", {"cmds": ["go build"]}, 1)

        assert len(violations) == 1
        assert violations[0].rule == "task-description"
        assert "desc:" in violations[0].suggested

    def test_private_task_no_check(self):
        """Test skips private tasks (starting with _)."""
        violations = check_task_description("_internal", {"cmds": ["echo"]}, 1)

        assert len(violations) == 0

    def test_non_dict_config(self):
        """Test handles non-dict task config."""
        violations = check_task_description("build", "string-config", 1)

        assert len(violations) == 0


class TestCheckPlatformSpecific:
    """Tests for check_platform_specific rule."""

    def test_with_platforms_ok(self):
        """Test no violation when platforms directive present."""
        task = {"platforms": ["linux", "darwin"], "cmds": ["rm -rf build/"]}
        violations = check_platform_specific("clean", task, 1)

        assert len(violations) == 0

    def test_unix_command_without_platforms(self):
        """Test detects Unix commands without platforms."""
        task = {"cmds": ["rm -rf build/", "chmod +x script.sh"]}
        violations = check_platform_specific("clean", task, 1)

        assert len(violations) >= 1
        assert any(v.rule == "platform-directive" for v in violations)

    def test_windows_command_without_platforms(self):
        """Test detects Windows commands without platforms."""
        task = {"cmds": ["del /q build\\*"]}
        violations = check_platform_specific("clean", task, 1)

        assert len(violations) == 1
        assert "windows" in violations[0].suggested.lower()

    def test_cross_platform_commands_ok(self):
        """Test no violation for cross-platform commands."""
        task = {"cmds": ["go build", "python script.py"]}
        violations = check_platform_specific("build", task, 1)

        assert len(violations) == 0

    def test_no_cmds(self):
        """Test handles task without cmds."""
        task = {"desc": "Just a description"}
        violations = check_platform_specific("info", task, 1)

        assert len(violations) == 0

    def test_non_dict_config(self):
        """Test handles non-dict task config."""
        violations = check_platform_specific("build", "string", 1)

        assert len(violations) == 0


class TestCheckSilentMode:
    """Tests for check_silent_mode rule."""

    def test_with_silent_ok(self):
        """Test no violation when silent present."""
        task = {"silent": True, "cmds": ["echo hello"]}
        violations = check_silent_mode("build", task, 1)

        assert len(violations) == 0

    def test_missing_silent(self):
        """Test suggests silent when missing."""
        task = {"cmds": ["echo hello"]}
        violations = check_silent_mode("build", task, 1)

        assert len(violations) == 1
        assert violations[0].rule == "silent-mode"
        assert violations[0].severity == Severity.INFO

    def test_no_cmds_no_suggestion(self):
        """Test no suggestion when no cmds."""
        task = {"desc": "Info task"}
        violations = check_silent_mode("info", task, 1)

        assert len(violations) == 0


class TestCheckAliases:
    """Tests for check_aliases rule."""

    def test_with_aliases_ok(self):
        """Test no violation when aliases present."""
        task = {"aliases": ["b"], "cmds": ["go build"]}
        violations = check_aliases("build", task, 1)

        assert len(violations) == 0

    def test_common_task_missing_alias(self):
        """Test suggests alias for common tasks."""
        task = {"cmds": ["go build"]}
        violations = check_aliases("build", task, 1)

        assert len(violations) == 1
        assert violations[0].rule == "task-aliases"
        assert "aliases:" in violations[0].suggested

    def test_uncommon_task_no_suggestion(self):
        """Test no suggestion for uncommon tasks."""
        task = {"cmds": ["echo hello"]}
        violations = check_aliases("my-custom-task", task, 1)

        assert len(violations) == 0

    def test_common_tasks_list(self):
        """Test all common tasks trigger suggestion."""
        common_tasks = ["build", "test", "run", "clean", "install", "deploy", "lint", "format"]

        for task_name in common_tasks:
            violations = check_aliases(task_name, {"cmds": ["cmd"]}, 1)
            assert len(violations) == 1, f"Expected violation for {task_name}"
