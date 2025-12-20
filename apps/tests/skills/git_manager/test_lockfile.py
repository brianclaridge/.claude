"""Tests for git lock file detection and cleanup."""

import time
from pathlib import Path

import pytest

from claude_apps.skills.git_manager.lockfile import (
    LockCleanResult,
    clean_locks,
    find_git_dir,
    find_lock_files,
    is_stale,
)


class TestFindGitDir:
    """Tests for find_git_dir function."""

    def test_regular_git_repo(self, tmp_path):
        """Test finding .git directory in regular repo."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = find_git_dir(tmp_path)
        assert result == git_dir

    def test_submodule_gitfile(self, tmp_path):
        """Test finding git dir from submodule .git file."""
        # Create actual gitdir location
        modules_dir = tmp_path / "parent" / ".git" / "modules" / "sub"
        modules_dir.mkdir(parents=True)

        # Create submodule with .git file pointing to gitdir
        sub_path = tmp_path / "submodule"
        sub_path.mkdir()
        gitfile = sub_path / ".git"
        gitfile.write_text(f"gitdir: {modules_dir}")

        result = find_git_dir(sub_path)
        assert result == modules_dir

    def test_submodule_relative_gitdir(self, tmp_path):
        """Test finding git dir with relative path in .git file."""
        # Create actual gitdir location
        modules_dir = tmp_path / ".git" / "modules" / "sub"
        modules_dir.mkdir(parents=True)

        # Create submodule with relative .git file
        sub_path = tmp_path / "submodule"
        sub_path.mkdir()
        gitfile = sub_path / ".git"
        gitfile.write_text("gitdir: ../.git/modules/sub")

        result = find_git_dir(sub_path)
        assert result is not None
        assert result.exists() or result == (sub_path / ".." / ".git" / "modules" / "sub").resolve()

    def test_no_git_dir(self, tmp_path):
        """Test when no .git exists."""
        result = find_git_dir(tmp_path)
        assert result is None


class TestFindLockFiles:
    """Tests for find_lock_files function."""

    def test_finds_index_lock(self, tmp_path):
        """Test finding index.lock."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 1
        assert locks[0].name == "index.lock"

    def test_finds_head_lock(self, tmp_path):
        """Test finding HEAD.lock."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 1
        assert locks[0].name == "HEAD.lock"

    def test_finds_config_lock(self, tmp_path):
        """Test finding config.lock."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 1
        assert locks[0].name == "config.lock"

    def test_finds_refs_locks(self, tmp_path):
        """Test finding locks in refs directory."""
        git_dir = tmp_path / ".git"
        refs_dir = git_dir / "refs" / "heads"
        refs_dir.mkdir(parents=True)
        (refs_dir / "main.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 1
        assert "main.lock" in locks[0].name

    def test_finds_module_locks(self, tmp_path):
        """Test finding locks in modules directory (submodules)."""
        git_dir = tmp_path / ".git"
        modules_dir = git_dir / "modules" / "sub"
        modules_dir.mkdir(parents=True)
        (modules_dir / "index.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 1

    def test_finds_multiple_locks(self, tmp_path):
        """Test finding multiple lock files."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()
        (git_dir / "HEAD.lock").touch()
        (git_dir / "config.lock").touch()

        locks = find_lock_files(git_dir)
        assert len(locks) == 3

    def test_no_locks(self, tmp_path):
        """Test when no lock files exist."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        locks = find_lock_files(git_dir)
        assert len(locks) == 0


class TestIsStale:
    """Tests for is_stale function."""

    def test_fresh_lock_not_stale(self, tmp_path):
        """Test that fresh lock is not stale."""
        lock = tmp_path / "index.lock"
        lock.touch()

        assert is_stale(lock, threshold=5) is False

    def test_old_lock_is_stale(self, tmp_path):
        """Test that old lock is stale."""
        lock = tmp_path / "index.lock"
        lock.touch()

        # Set mtime to 10 seconds ago
        old_time = time.time() - 10
        import os
        os.utime(lock, (old_time, old_time))

        assert is_stale(lock, threshold=5) is True

    def test_nonexistent_lock(self, tmp_path):
        """Test with nonexistent file."""
        lock = tmp_path / "nonexistent.lock"
        assert is_stale(lock) is False


class TestCleanLocks:
    """Tests for clean_locks function."""

    def test_no_git_repo(self, tmp_path):
        """Test cleaning non-git directory."""
        result = clean_locks(tmp_path)

        assert result.cleaned is False
        assert "Not a git repository" in result.error
        assert result.exit_code == 1

    def test_no_locks_to_clean(self, tmp_path):
        """Test cleaning when no locks exist."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = clean_locks(tmp_path)

        assert result.cleaned is True
        assert len(result.files_removed) == 0
        assert result.exit_code == 0

    def test_force_removes_fresh_lock(self, tmp_path):
        """Test that force=True removes fresh locks."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        lock = git_dir / "index.lock"
        lock.touch()

        result = clean_locks(tmp_path, force=True)

        assert result.cleaned is True
        assert "index.lock" in result.files_removed
        assert not lock.exists()

    def test_skips_fresh_lock_without_force(self, tmp_path):
        """Test that fresh locks are skipped without force."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        lock = git_dir / "index.lock"
        lock.touch()

        result = clean_locks(tmp_path, force=False)

        assert lock.exists()
        assert "index.lock" in result.files_skipped

    def test_removes_stale_lock(self, tmp_path):
        """Test that stale locks are removed."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        lock = git_dir / "index.lock"
        lock.touch()

        # Make lock stale
        old_time = time.time() - 10
        import os
        os.utime(lock, (old_time, old_time))

        result = clean_locks(tmp_path)

        assert result.cleaned is True
        assert "index.lock" in result.files_removed
        assert not lock.exists()

    def test_dry_run(self, tmp_path):
        """Test dry run mode."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        lock = git_dir / "index.lock"
        lock.touch()

        result = clean_locks(tmp_path, force=True, dry_run=True)

        assert result.cleaned is True
        assert "index.lock" in result.files_removed
        assert lock.exists()  # Should still exist

    def test_default_repo_path(self, tmp_path, monkeypatch):
        """Test using current directory as default."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        monkeypatch.chdir(tmp_path)
        result = clean_locks()

        assert result.cleaned is True
        assert result.exit_code == 0


class TestLockCleanResult:
    """Tests for LockCleanResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dict."""
        result = LockCleanResult(
            cleaned=True,
            files_removed=["index.lock"],
            files_skipped=["HEAD.lock"],
            error=None,
            exit_code=0,
        )

        d = result.to_dict()

        assert d["cleaned"] is True
        assert d["files_removed"] == ["index.lock"]
        assert d["files_skipped"] == ["HEAD.lock"]
        assert d["error"] is None
        assert d["exit_code"] == 0

    def test_to_dict_with_error(self):
        """Test serialization with error."""
        result = LockCleanResult(
            cleaned=False,
            error="Something went wrong",
            exit_code=1,
        )

        d = result.to_dict()

        assert d["cleaned"] is False
        assert d["error"] == "Something went wrong"
