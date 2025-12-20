"""Tests for gomplate validation rules based on Rule 095."""

from pathlib import Path

import pytest

from claude_apps.skills.gomplate_manager.rules import (
    check_getenv_usage,
    check_output_paths,
    check_template_whitespace,
    run_all_rules,
)


class TestCheckGetenvUsage:
    """Tests for check_getenv_usage rule."""

    def test_no_getenv(self):
        """Test no violations when using .Env."""
        content = '{{ .Env.FOO }}\n{{ .Env.BAR }}'
        violations = check_getenv_usage(content, "template.tmpl")

        assert len(violations) == 0

    def test_detects_getenv(self):
        """Test detects getenv usage."""
        content = '{{ getenv "FOO" }}'
        violations = check_getenv_usage(content, "template.tmpl")

        assert len(violations) == 1
        assert violations[0]["rule"] == "env-access-style"
        assert violations[0]["severity"] == "warning"
        assert "FOO" in violations[0]["message"]

    def test_detects_multiple_getenv(self):
        """Test detects multiple getenv usages."""
        content = '''
line1 {{ getenv "FOO" }}
line2 {{ getenv "BAR" }}
line3 {{ .Env.OK }}
'''
        violations = check_getenv_usage(content, "template.tmpl")

        assert len(violations) == 2

    def test_provides_correct_line_numbers(self):
        """Test provides correct line numbers."""
        content = '''
line1
{{ getenv "FOO" }}
line3
'''
        violations = check_getenv_usage(content, "template.tmpl")

        assert violations[0]["line"] == 3

    def test_suggests_env_syntax(self):
        """Test suggests .Env syntax."""
        content = '{{ getenv "MYVAR" }}'
        violations = check_getenv_usage(content, "template.tmpl")

        assert "{{ .Env.MYVAR }}" in violations[0]["suggested"]

    def test_includes_file_path(self):
        """Test includes file path in violation."""
        content = '{{ getenv "FOO" }}'
        violations = check_getenv_usage(content, "/path/to/template.tmpl")

        assert violations[0]["file"] == "/path/to/template.tmpl"


class TestCheckTemplateWhitespace:
    """Tests for check_template_whitespace rule."""

    def test_proper_whitespace(self):
        """Test no violations with proper whitespace."""
        content = "{{ .Env.FOO }}\n{{- .Env.BAR -}}"
        violations = check_template_whitespace(content, "template.tmpl")

        assert len(violations) == 0

    def test_detects_compact_style(self):
        """Test detects compact style without spaces."""
        content = "{{.Env.FOO}}"
        violations = check_template_whitespace(content, "template.tmpl")

        assert len(violations) == 1
        assert violations[0]["rule"] == "template-whitespace"
        assert violations[0]["severity"] == "info"

    def test_allows_trim_markers(self):
        """Test allows trim markers at start."""
        content = "{{- .Env.FOO }}"
        violations = check_template_whitespace(content, "template.tmpl")

        assert len(violations) == 0

    def test_detects_on_multiple_lines(self):
        """Test detects violations on multiple lines."""
        content = "{{.A}}\n{{ .B }}\n{{.C}}"
        violations = check_template_whitespace(content, "template.tmpl")

        assert len(violations) == 2  # .A and .C

    def test_correct_line_numbers(self):
        """Test provides correct line numbers."""
        content = "{{ ok }}\n{{bad}}\n{{ ok }}"
        violations = check_template_whitespace(content, "template.tmpl")

        assert violations[0]["line"] == 2


class TestCheckOutputPaths:
    """Tests for check_output_paths rule."""

    def test_absolute_paths_ok(self):
        """Test no violations for absolute paths."""
        config = {
            "outputFiles": ["/root/.config/app.json", "/etc/app/config.yaml"]
        }
        violations = check_output_paths(config)

        assert len(violations) == 0

    def test_detects_relative_paths(self):
        """Test detects relative paths."""
        config = {
            "outputFiles": ["config/app.json", "./output.txt"]
        }
        violations = check_output_paths(config)

        assert len(violations) == 2
        assert violations[0]["rule"] == "output-path-absolute"

    def test_suggests_absolute_path(self):
        """Test suggests absolute path."""
        config = {
            "outputFiles": ["output.txt"]
        }
        violations = check_output_paths(config)

        assert violations[0]["suggested"] == "/output.txt"

    def test_no_output_files(self):
        """Test handles missing outputFiles key."""
        config = {"inputDir": "templates/"}
        violations = check_output_paths(config)

        assert len(violations) == 0

    def test_empty_output_files(self):
        """Test handles empty outputFiles list."""
        config = {"outputFiles": []}
        violations = check_output_paths(config)

        assert len(violations) == 0


class TestRunAllRules:
    """Tests for run_all_rules function."""

    def test_empty_config(self, tmp_path):
        """Test with empty config."""
        config = {}
        violations = run_all_rules(config, tmp_path)

        assert violations == []

    def test_runs_template_rules(self, tmp_path):
        """Test runs rules on template files."""
        # Create template with violations
        template = tmp_path / "template.tmpl"
        template.write_text('{{ getenv "FOO" }}')

        config = {
            "inputFiles": ["template.tmpl"],
            "outputFiles": ["/output.txt"],
        }

        violations = run_all_rules(config, tmp_path)

        # Should have getenv violation
        assert any(v["rule"] == "env-access-style" for v in violations)

    def test_runs_output_path_rules(self, tmp_path):
        """Test runs output path rules."""
        config = {
            "inputFiles": [],
            "outputFiles": ["relative/path.txt"],
        }

        violations = run_all_rules(config, tmp_path)

        assert any(v["rule"] == "output-path-absolute" for v in violations)

    def test_handles_input_dir(self, tmp_path):
        """Test handles inputDir configuration."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "a.tmpl").write_text("{{ .Env.A }}")
        (templates_dir / "b.tmpl").write_text('{{ getenv "B" }}')

        config = {
            "inputDir": "templates",
            "outputDir": "/output/",
        }

        violations = run_all_rules(config, tmp_path)

        # Should have one getenv violation from b.tmpl
        assert any(v["rule"] == "env-access-style" for v in violations)

    def test_skips_nonexistent_files(self, tmp_path):
        """Test skips non-existent template files."""
        config = {
            "inputFiles": ["nonexistent.tmpl"],
            "outputFiles": ["/output.txt"],
        }

        violations = run_all_rules(config, tmp_path)

        # Should not raise, just skip
        assert isinstance(violations, list)

    def test_skips_directories(self, tmp_path):
        """Test skips directories in file list."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        config = {
            "inputFiles": ["subdir"],
            "outputFiles": ["/output/"],
        }

        violations = run_all_rules(config, tmp_path)

        # Should not raise
        assert isinstance(violations, list)

    def test_combines_all_violations(self, tmp_path):
        """Test combines violations from all rules."""
        template = tmp_path / "template.tmpl"
        template.write_text('{{getenv "FOO"}}')  # Both violations

        config = {
            "inputFiles": ["template.tmpl"],
            "outputFiles": ["relative.txt"],  # Output violation
        }

        violations = run_all_rules(config, tmp_path)

        rules = {v["rule"] for v in violations}
        assert "env-access-style" in rules
        assert "template-whitespace" in rules
        assert "output-path-absolute" in rules
