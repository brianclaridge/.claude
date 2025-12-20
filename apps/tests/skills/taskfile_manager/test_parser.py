"""Tests for Taskfile parser and validation."""

from pathlib import Path

import pytest

from claude_apps.skills.taskfile_manager.parser import (
    find_line_number,
    parse_taskfile,
    validate_taskfile,
)
from claude_apps.skills.taskfile_manager.rules import Severity


class TestParseTaskfile:
    """Tests for parse_taskfile function."""

    def test_parses_valid_taskfile(self, tmp_path):
        """Test parsing valid Taskfile."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
vars:
  NAME: myapp
tasks:
  build:
    cmds:
      - go build
""")

        content, raw_lines = parse_taskfile(taskfile)

        assert content["version"] == "3"
        assert "NAME" in content["vars"]
        assert "build" in content["tasks"]
        assert len(raw_lines) > 0

    def test_returns_raw_lines(self, tmp_path):
        """Test that raw lines are returned."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("line1\nline2\nline3")

        _, raw_lines = parse_taskfile(taskfile)

        assert raw_lines == ["line1", "line2", "line3"]


class TestFindLineNumber:
    """Tests for find_line_number function."""

    def test_finds_key(self):
        """Test finding a key."""
        lines = ["version: '3'", "vars:", "  NAME: value", "tasks:"]
        line_num = find_line_number(lines, "vars")

        assert line_num == 2

    def test_finds_nested_key(self):
        """Test finding a nested key."""
        lines = ["tasks:", "  build:", "    cmds:"]
        line_num = find_line_number(lines, "build")

        assert line_num == 2

    def test_with_start_line(self):
        """Test searching from start line."""
        lines = ["vars:", "  NAME: a", "tasks:", "  build:"]
        line_num = find_line_number(lines, "build", start_line=2)

        assert line_num == 4

    def test_not_found_returns_default(self):
        """Test returns start line + 1 when not found."""
        lines = ["vars:", "  NAME: a"]
        line_num = find_line_number(lines, "nonexistent", start_line=0)

        assert line_num == 1


class TestValidateTaskfile:
    """Tests for validate_taskfile function."""

    def test_valid_taskfile_no_violations(self, tmp_path):
        """Test valid Taskfile has no errors."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
vars:
  BUILD_DIR: ./dist
tasks:
  build:
    desc: Build the application
    silent: true
    aliases: [b]
    cmds:
      - go build -o {{.BUILD_DIR}}/app
""")

        violations = validate_taskfile(taskfile)

        # Should have no ERROR or WARNING (only INFO is acceptable)
        errors = [v for v in violations if v.severity in (Severity.ERROR, Severity.WARNING)]
        assert len(errors) == 0

    def test_detects_lowercase_variable(self, tmp_path):
        """Test detects lowercase variable."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
vars:
  build_dir: ./dist
tasks:
  build:
    desc: Build
    cmds:
      - echo done
""")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "variable-uppercase" for v in violations)

    def test_detects_template_whitespace(self, tmp_path):
        """Test detects template whitespace."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
vars:
  NAME: app
tasks:
  build:
    desc: Build
    cmds:
      - echo {{ .NAME }}
""")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "template-whitespace" for v in violations)

    def test_detects_missing_description(self, tmp_path):
        """Test detects missing task description."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
tasks:
  build:
    cmds:
      - echo build
""")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "task-description" for v in violations)

    def test_detects_bad_task_naming(self, tmp_path):
        """Test detects bad task naming."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
tasks:
  buildApp:
    desc: Build
    cmds:
      - echo build
""")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "task-kebab-case" for v in violations)

    def test_detects_platform_specific(self, tmp_path):
        """Test detects platform-specific commands."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
tasks:
  clean:
    desc: Clean
    cmds:
      - rm -rf build/
""")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "platform-directive" for v in violations)

    def test_handles_empty_file(self, tmp_path):
        """Test handles empty file."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "empty-file" for v in violations)

    def test_handles_invalid_yaml(self, tmp_path):
        """Test handles invalid YAML."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("{ invalid yaml [[[")

        violations = validate_taskfile(taskfile)

        assert any(v.rule == "parse-error" for v in violations)

    def test_violations_sorted_by_line(self, tmp_path):
        """Test violations are sorted by line number."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
vars:
  bad: 1
tasks:
  ugly:
    cmds:
      - echo done
""")

        violations = validate_taskfile(taskfile)

        lines = [v.line for v in violations]
        assert lines == sorted(lines)

    def test_skips_private_tasks(self, tmp_path):
        """Test skips private tasks for description check."""
        taskfile = tmp_path / "Taskfile.yml"
        taskfile.write_text("""
version: '3'
tasks:
  _internal:
    cmds:
      - echo private
""")

        violations = validate_taskfile(taskfile)

        # Should not complain about missing desc for _internal
        desc_violations = [v for v in violations if v.rule == "task-description"]
        assert len(desc_violations) == 0
