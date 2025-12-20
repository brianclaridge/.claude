"""Tests for commit message generation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.git_manager.message import (
    MessageResult,
    get_diff_stat,
    infer_scope,
    infer_type,
    generate_message,
)
from claude_apps.skills.git_manager.plan import PlanInfo


class TestMessageResult:
    """Tests for MessageResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = MessageResult()

        assert result.type == "chore"
        assert result.scope is None
        assert result.subject == ""
        assert result.body == ""
        assert result.full_message == ""
        assert result.files_changed == 0
        assert result.plan_reference is None
        assert result.exit_code == 0
        assert result.error is None
        assert result.session_stats is None

    def test_to_dict(self):
        """Test serialization."""
        result = MessageResult(
            type="feat",
            scope="auth",
            subject="add login",
            body="Body text",
            full_message="feat(auth): add login\n\nBody text",
            files_changed=5,
            plan_reference="auth-feature",
            session_stats={"tokens": 100},
        )

        d = result.to_dict()

        assert d["type"] == "feat"
        assert d["scope"] == "auth"
        assert d["subject"] == "add login"
        assert d["body"] == "Body text"
        assert d["full_message"] == "feat(auth): add login\n\nBody text"
        assert d["files_changed"] == 5
        assert d["plan_reference"] == "auth-feature"
        assert d["session_stats"] == {"tokens": 100}


class TestGetDiffStat:
    """Tests for get_diff_stat function."""

    def test_returns_staged_files(self, tmp_path, monkeypatch):
        """Test getting staged files."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "src/auth.py\nsrc/login.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        files, count = get_diff_stat(tmp_path)

        assert count == 2
        assert "src/auth.py" in files
        assert "src/login.py" in files

    def test_fallback_to_unstaged(self, tmp_path, monkeypatch):
        """Test fallback to unstaged when no staged files."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = ""
                return MockResult()
            if "--name-only" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "modified.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        files, count = get_diff_stat(tmp_path)

        assert count == 1
        assert "modified.py" in files

    def test_fallback_to_status(self, tmp_path, monkeypatch):
        """Test fallback to git status for untracked files."""
        import subprocess

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            cmd = args[0]
            # First call: git diff --cached --name-only (empty, but code returns early)
            if call_count[0] == 1:
                class MockResult:
                    returncode = 0
                    stdout = ""
                return MockResult()
            # Second call: git diff --name-only (fail to trigger status fallback)
            if call_count[0] == 2:
                class MockResult:
                    returncode = 1  # Fail to trigger fallback to status
                    stdout = ""
                return MockResult()
            # Third call: git status --porcelain
            class MockResult:
                returncode = 0
                stdout = "?? new_file.py\nA  staged.py\n"
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        files, count = get_diff_stat(tmp_path)

        assert count == 2
        assert "new_file.py" in files

    def test_handles_failure(self, tmp_path, monkeypatch):
        """Test handles command failure."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("git", 10)

        monkeypatch.setattr(subprocess, "run", mock_run)

        files, count = get_diff_stat(tmp_path)

        assert files == []
        assert count == 0


class TestInferScope:
    """Tests for infer_scope function."""

    def test_infers_auth_scope(self):
        """Test inferring auth scope."""
        files = ["src/auth/login.py", "src/auth/session.py"]
        assert infer_scope(files) == "auth"

    def test_infers_api_scope(self):
        """Test inferring api scope."""
        files = ["api/routes/users.py", "api/endpoint.py"]
        assert infer_scope(files) == "api"

    def test_infers_ui_scope(self):
        """Test inferring ui scope."""
        files = ["components/Button.tsx", "pages/Home.tsx"]
        assert infer_scope(files) == "ui"

    def test_infers_db_scope(self):
        """Test inferring db scope."""
        files = ["models/user.py", "migrations/001.sql"]
        assert infer_scope(files) == "db"

    def test_infers_config_scope(self):
        """Test inferring config scope."""
        files = ["config/settings.yaml", ".env.example"]
        assert infer_scope(files) == "config"

    def test_infers_test_scope(self):
        """Test inferring test scope."""
        # Use filenames that only match test pattern, not auth
        files = ["tests/test_utils.py", "tests/test_helpers.py"]
        assert infer_scope(files) == "test"

    def test_infers_skill_scope(self):
        """Test inferring skill scope."""
        files = ["skills/git-manager/SKILL.md"]
        assert infer_scope(files) == "skill"

    def test_infers_agent_scope(self):
        """Test inferring agent scope."""
        files = ["agents/code-reviewer/agent.md"]
        assert infer_scope(files) == "agent"

    def test_infers_hook_scope(self):
        """Test inferring hook scope."""
        files = ["hooks/pre-commit.py"]
        assert infer_scope(files) == "hook"

    def test_infers_docs_scope(self):
        """Test inferring docs scope."""
        files = ["docs/README.md", "CHANGELOG.md"]
        assert infer_scope(files) == "docs"

    def test_returns_highest_score(self):
        """Test returns scope with highest score."""
        files = ["tests/test_auth.py", "tests/test_login.py", "src/auth.py"]
        # test appears in 2 files, auth in 2 files, but test is more specific
        assert infer_scope(files) in ["test", "auth"]

    def test_returns_none_for_no_match(self):
        """Test returns None when no patterns match."""
        files = ["random_file.xyz", "another.abc"]
        assert infer_scope(files) is None


class TestInferType:
    """Tests for infer_type function."""

    def test_infers_fix_from_plan(self):
        """Test inferring fix type from plan objective."""
        plan = PlanInfo(path=Path("test"), objective="Fix login bug")
        assert infer_type(plan, []) == "fix"

    def test_infers_feat_from_plan(self):
        """Test inferring feat type from plan objective."""
        plan = PlanInfo(path=Path("test"), objective="Add new feature")
        assert infer_type(plan, []) == "feat"

    def test_infers_refactor_from_plan(self):
        """Test inferring refactor type from plan objective."""
        plan = PlanInfo(path=Path("test"), objective="Refactor authentication module")
        assert infer_type(plan, []) == "refactor"

    def test_infers_docs_from_plan(self):
        """Test inferring docs type from plan objective."""
        plan = PlanInfo(path=Path("test"), objective="Document the API")
        assert infer_type(plan, []) == "docs"

    def test_infers_test_from_plan(self):
        """Test inferring test type from plan objective."""
        # Note: "Add" keyword triggers "feat" first, so use objective without add/implement/create/new
        plan = PlanInfo(path=Path("test"), objective="Write test coverage for auth")
        assert infer_type(plan, []) == "test"

    def test_infers_test_from_files(self):
        """Test inferring test type from all test files."""
        files = ["tests/test_auth.py", "tests/test_login.py"]
        assert infer_type(None, files) == "test"

    def test_infers_docs_from_files(self):
        """Test inferring docs type from all doc files."""
        files = ["docs/README.md", "docs/API.md"]
        assert infer_type(None, files) == "docs"

    def test_defaults_to_chore(self):
        """Test defaults to chore type."""
        assert infer_type(None, []) == "chore"
        assert infer_type(None, ["random.py"]) == "chore"

    def test_plan_takes_precedence(self):
        """Test plan objective takes precedence over file inference."""
        plan = PlanInfo(path=Path("test"), objective="Fix critical bug")
        files = ["tests/test_fix.py"]  # Would normally be "test"
        assert infer_type(plan, files) == "fix"


class TestGenerateMessage:
    """Tests for generate_message function."""

    def test_returns_error_for_no_changes(self, tmp_path, monkeypatch):
        """Test returns error when no changes detected."""
        import subprocess

        def mock_run(*args, **kwargs):
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path)

        assert result.exit_code == 1
        assert "No changes" in result.error

    def test_generates_basic_message(self, tmp_path, monkeypatch):
        """Test generating basic message without plan."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "src/app.py\nsrc/utils.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path)

        assert result.exit_code == 0
        assert result.files_changed == 2
        assert result.type == "chore"
        assert "update 2 files" in result.subject
        assert result.full_message != ""

    def test_uses_plan_for_message(self, tmp_path, monkeypatch):
        """Test using plan info for message generation."""
        import subprocess

        # Create plan file
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_file = plans_dir / "20250115_120000_auth-feature.md"
        plan_file.write_text(
            "# Plan: Implement authentication\n\n"
            "## Summary\n"
            "Adding OAuth2 authentication.\n\n"
            "## TODO\n"
            "- [x] Add login endpoint\n"
            "- [x] Add logout endpoint\n"
        )

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "src/auth/login.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path, plans_dir=plans_dir)

        assert result.exit_code == 0
        assert result.type == "feat"  # From "Implement" keyword
        assert result.plan_reference == "auth-feature"
        assert "authentication" in result.subject.lower()

    def test_includes_scope_in_message(self, tmp_path, monkeypatch):
        """Test scope is included in full message."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "src/auth/login.py\nsrc/auth/session.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path)

        assert result.scope == "auth"
        assert "(auth)" in result.full_message

    def test_includes_files_modified_section(self, tmp_path, monkeypatch):
        """Test files modified section in body."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "file1.py\nfile2.py\nfile3.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path)

        assert "Files Modified" in result.body
        assert "3 files changed" in result.body

    def test_truncates_long_subject(self, tmp_path, monkeypatch):
        """Test subject is truncated to 50 chars."""
        import subprocess

        # Create plan with long objective
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_file = plans_dir / "20250115_120000_long-objective.md"
        plan_file.write_text(
            "# Plan: This is a very long objective that should be truncated to fifty characters\n"
        )

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "file.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path, plans_dir=plans_dir)

        assert len(result.subject) <= 50

    def test_strips_action_prefix_from_subject(self, tmp_path, monkeypatch):
        """Test action prefixes are stripped from subject."""
        import subprocess

        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_file = plans_dir / "20250115_120000_feature.md"
        plan_file.write_text("# Plan: Implement the new feature\n")

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "file.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path, plans_dir=plans_dir)

        # "Implement " should be stripped
        assert not result.subject.lower().startswith("implement")

    def test_includes_session_stats(self, tmp_path, monkeypatch):
        """Test session stats are included."""
        import subprocess

        def mock_run(*args, **kwargs):
            cmd = args[0]
            if "--cached" in cmd:
                class MockResult:
                    returncode = 0
                    stdout = "file.py\n"
                return MockResult()
            class MockResult:
                returncode = 0
                stdout = ""
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = generate_message(tmp_path)

        assert result.session_stats is not None
        assert isinstance(result.session_stats, dict)
