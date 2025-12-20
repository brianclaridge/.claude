"""Tests for language detection collector."""

from pathlib import Path

import pytest

from claude_apps.skills.project_metadata_builder.collectors.lang_collector import (
    EXTENSION_MAP,
    IGNORE_DIRS,
    collect_languages,
)


class TestExtensionMap:
    """Tests for extension to language mapping."""

    def test_python_extensions(self):
        """Test Python file extensions."""
        assert EXTENSION_MAP[".py"] == "Python"

    def test_javascript_extensions(self):
        """Test JavaScript file extensions."""
        assert EXTENSION_MAP[".js"] == "JavaScript"
        assert EXTENSION_MAP[".jsx"] == "JavaScript"

    def test_typescript_extensions(self):
        """Test TypeScript file extensions."""
        assert EXTENSION_MAP[".ts"] == "TypeScript"
        assert EXTENSION_MAP[".tsx"] == "TypeScript"

    def test_shell_extensions(self):
        """Test shell script extensions."""
        assert EXTENSION_MAP[".sh"] == "Shell"
        assert EXTENSION_MAP[".bash"] == "Shell"
        assert EXTENSION_MAP[".zsh"] == "Shell"

    def test_config_extensions(self):
        """Test config file extensions."""
        assert EXTENSION_MAP[".yml"] == "YAML"
        assert EXTENSION_MAP[".yaml"] == "YAML"
        assert EXTENSION_MAP[".json"] == "JSON"
        assert EXTENSION_MAP[".toml"] == "TOML"


class TestIgnoreDirs:
    """Tests for ignored directory patterns."""

    def test_git_ignored(self):
        """Test .git is ignored."""
        assert ".git" in IGNORE_DIRS

    def test_venv_ignored(self):
        """Test virtual environments are ignored."""
        assert "venv" in IGNORE_DIRS
        assert ".venv" in IGNORE_DIRS

    def test_node_modules_ignored(self):
        """Test node_modules is ignored."""
        assert "node_modules" in IGNORE_DIRS

    def test_pycache_ignored(self):
        """Test __pycache__ is ignored."""
        assert "__pycache__" in IGNORE_DIRS


class TestCollectLanguages:
    """Tests for collect_languages function."""

    def test_empty_directory(self, tmp_path):
        """Test empty directory returns empty languages."""
        result = collect_languages(tmp_path)

        assert result.primary is None
        assert result.all == {}

    def test_detects_single_language(self, tmp_path):
        """Test detecting a single language."""
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        result = collect_languages(tmp_path)

        assert result.primary == "Python"
        assert "Python" in result.all
        assert result.all["Python"] == 1.0

    def test_detects_multiple_languages(self, tmp_path):
        """Test detecting multiple languages."""
        (tmp_path / "main.py").write_text("a" * 100)  # 100 bytes Python
        (tmp_path / "app.js").write_text("b" * 50)  # 50 bytes JavaScript

        result = collect_languages(tmp_path)

        assert result.primary == "Python"  # Most bytes
        assert "Python" in result.all
        assert "JavaScript" in result.all
        # Python should be ~66%, JavaScript ~33%
        assert result.all["Python"] > result.all["JavaScript"]

    def test_ignores_git_directory(self, tmp_path):
        """Test .git directory is ignored."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.py").write_text("a" * 1000)
        (tmp_path / "main.js").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "JavaScript"
        assert "Python" not in result.all

    def test_ignores_node_modules(self, tmp_path):
        """Test node_modules is ignored."""
        node_dir = tmp_path / "node_modules"
        node_dir.mkdir()
        (node_dir / "package.js").write_text("a" * 1000)
        (tmp_path / "main.py").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"

    def test_ignores_venv(self, tmp_path):
        """Test venv directory is ignored."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "pip.py").write_text("a" * 1000)
        (tmp_path / "main.go").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Go"

    def test_handles_nested_directories(self, tmp_path):
        """Test handles nested directory structure."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("a" * 100)

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_app.py").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"
        assert result.all["Python"] == 1.0

    def test_case_insensitive_extension(self, tmp_path):
        """Test extension matching is case insensitive."""
        (tmp_path / "main.PY").write_text("a" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"

    def test_unknown_extensions_ignored(self, tmp_path):
        """Test unknown file extensions are ignored."""
        (tmp_path / "data.xyz").write_text("a" * 1000)
        (tmp_path / "main.py").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"
        assert len(result.all) == 1

    def test_handles_empty_files(self, tmp_path):
        """Test handles empty files gracefully."""
        (tmp_path / "empty.py").write_text("")
        (tmp_path / "main.py").write_text("a" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"

    def test_ignores_hidden_directories(self, tmp_path):
        """Test directories starting with . are ignored."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.js").write_text("a" * 1000)
        (tmp_path / "main.py").write_text("b" * 100)

        result = collect_languages(tmp_path)

        assert result.primary == "Python"
        assert "JavaScript" not in result.all
