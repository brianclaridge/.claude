"""Check remote repository authentication status."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()

# Container-specific auth command
GH_AUTH_COMMAND = "gh auth login --git-protocol https --web"


@dataclass
class AuthResult:
    """Result of authentication check."""

    remote_url: Optional[str] = None
    remote_type: str = "unknown"  # "https", "ssh", "local"
    authenticated: bool = False
    auth_method: Optional[str] = None  # "gh", "ssh-key", "token"
    needs_auth: bool = False
    exit_code: int = 0
    error: Optional[str] = None
    guidance: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "remote_url": self.remote_url,
            "remote_type": self.remote_type,
            "authenticated": self.authenticated,
            "auth_method": self.auth_method,
            "needs_auth": self.needs_auth,
            "error": self.error,
            "guidance": self.guidance,
        }


def get_remote_url(repo_path: Path) -> Optional[str]:
    """Get origin remote URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("get_remote_failed", error=str(e))
    return None


def detect_remote_type(url: str) -> str:
    """Detect if remote is HTTPS, SSH, or local."""
    if url.startswith("https://"):
        return "https"
    if url.startswith("git@") or url.startswith("ssh://"):
        return "ssh"
    if url.startswith("/") or url.startswith("file://"):
        return "local"
    return "unknown"


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_ssh_auth() -> bool:
    """Check if SSH key auth works for GitHub."""
    try:
        result = subprocess.run(
            ["ssh", "-T", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # GitHub returns exit code 1 but "successfully authenticated" in stderr
        return "successfully authenticated" in result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_auth(repo_path: Path) -> AuthResult:
    """Check authentication status for remote repository."""
    result = AuthResult()

    # Get remote URL
    url = get_remote_url(repo_path)
    if not url:
        result.exit_code = 1
        result.error = "No remote 'origin' configured"
        return result

    result.remote_url = url
    result.remote_type = detect_remote_type(url)

    # Check based on remote type
    if result.remote_type == "ssh":
        # SSH remotes use SSH key authentication
        if check_ssh_auth():
            result.authenticated = True
            result.auth_method = "ssh-key"
            result.exit_code = 0
        else:
            result.authenticated = False
            result.needs_auth = True
            result.exit_code = 1
            result.error = "SSH authentication failed"
            result.guidance = "Ensure SSH key is loaded: ssh-add -l"

    elif result.remote_type == "https":
        # HTTPS GitHub remotes should use gh auth
        is_github = "github.com" in url

        if is_github:
            if check_gh_auth():
                result.authenticated = True
                result.auth_method = "gh"
                result.exit_code = 0
            else:
                result.authenticated = False
                result.needs_auth = True
                result.exit_code = 1
                result.error = "GitHub CLI not authenticated"
                result.guidance = f"Run: {GH_AUTH_COMMAND}"
        else:
            # Non-GitHub HTTPS - assume credential helper
            result.authenticated = True  # Optimistic
            result.auth_method = "credential-helper"
            result.exit_code = 0

    elif result.remote_type == "local":
        # Local remotes don't need auth
        result.authenticated = True
        result.auth_method = "none"
        result.exit_code = 0

    else:
        result.exit_code = 1
        result.error = f"Unknown remote type: {url}"

    return result
