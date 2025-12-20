"""Tests for dependency collection."""

import json
from pathlib import Path

import pytest

from claude_apps.skills.project_metadata_builder.collectors.deps_collector import (
    collect_dependencies,
)


class TestCollectDependencies:
    """Tests for collect_dependencies function."""

    def test_empty_directory(self, tmp_path):
        """Test empty directory returns empty deps."""
        result = collect_dependencies(tmp_path)

        assert result.python == []
        assert result.node == []


class TestPythonDependencies:
    """Tests for Python dependency collection."""

    def test_parses_pyproject_toml(self, tmp_path):
        """Test parsing pyproject.toml dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[project]
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
    "structlog",
]
''')

        result = collect_dependencies(tmp_path)

        assert "requests>=2.28" in result.python
        assert "pydantic>=2.0" in result.python
        assert "structlog" in result.python

    def test_parses_requirements_txt(self, tmp_path):
        """Test parsing requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text('''
requests==2.28.0
pytest>=7.0
# Comment line
-e ./local-package

Flask
''')

        result = collect_dependencies(tmp_path)

        assert "requests==2.28.0" in result.python
        assert "pytest>=7.0" in result.python
        assert "Flask" in result.python
        # Should skip comments and -e lines
        assert not any("Comment" in d for d in result.python)
        assert not any("-e" in d for d in result.python)

    def test_combines_pyproject_and_requirements(self, tmp_path):
        """Test combining dependencies from both files."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[project]
dependencies = ["requests"]
''')

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("pytest\n")

        result = collect_dependencies(tmp_path)

        assert "requests" in result.python
        assert "pytest" in result.python

    def test_deduplicates_dependencies(self, tmp_path):
        """Test that duplicate dependencies are removed."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[project]
dependencies = ["requests"]
''')

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests\n")

        result = collect_dependencies(tmp_path)

        # Should only have one entry
        assert result.python.count("requests") == 1

    def test_collects_from_claude_skills(self, tmp_path):
        """Test collecting from .claude/skills subdirectory."""
        skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)

        pyproject = skill_dir / "pyproject.toml"
        pyproject.write_text('''
[project]
dependencies = ["structlog"]
''')

        result = collect_dependencies(tmp_path)

        assert "structlog" in result.python

    def test_handles_malformed_pyproject(self, tmp_path):
        """Test handles malformed pyproject.toml gracefully."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("not valid toml [[[")

        result = collect_dependencies(tmp_path)

        # Should not raise, returns empty
        assert result.python == []


class TestNodeDependencies:
    """Tests for Node.js dependency collection."""

    def test_parses_package_json(self, tmp_path):
        """Test parsing package.json dependencies."""
        package = tmp_path / "package.json"
        package.write_text(json.dumps({
            "name": "my-app",
            "dependencies": {
                "react": "^18.0.0",
                "next": "^14.0.0",
            }
        }))

        result = collect_dependencies(tmp_path)

        assert "react@^18.0.0" in result.node
        assert "next@^14.0.0" in result.node

    def test_includes_dev_dependencies(self, tmp_path):
        """Test includes devDependencies."""
        package = tmp_path / "package.json"
        package.write_text(json.dumps({
            "name": "my-app",
            "dependencies": {
                "react": "^18.0.0",
            },
            "devDependencies": {
                "typescript": "^5.0.0",
            }
        }))

        result = collect_dependencies(tmp_path)

        assert "react@^18.0.0" in result.node
        assert "typescript@^5.0.0" in result.node

    def test_includes_peer_dependencies(self, tmp_path):
        """Test includes peerDependencies."""
        package = tmp_path / "package.json"
        package.write_text(json.dumps({
            "name": "my-library",
            "peerDependencies": {
                "react": ">=17.0.0",
            }
        }))

        result = collect_dependencies(tmp_path)

        assert "react@>=17.0.0" in result.node

    def test_handles_missing_package_json(self, tmp_path):
        """Test handles missing package.json."""
        result = collect_dependencies(tmp_path)

        assert result.node == []

    def test_handles_malformed_package_json(self, tmp_path):
        """Test handles malformed package.json gracefully."""
        package = tmp_path / "package.json"
        package.write_text("{ invalid json }")

        result = collect_dependencies(tmp_path)

        assert result.node == []

    def test_handles_package_json_without_deps(self, tmp_path):
        """Test handles package.json without dependencies."""
        package = tmp_path / "package.json"
        package.write_text(json.dumps({
            "name": "my-app",
            "version": "1.0.0",
        }))

        result = collect_dependencies(tmp_path)

        assert result.node == []
