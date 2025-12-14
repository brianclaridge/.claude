"""Git identity detection cascade."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class IdentityResult:
    """Result of identity detection."""

    name: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None  # "env", "ssh", "gh", "git-config"
    detected: bool = False
    needs_input: bool = False
    exit_code: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "source": self.source,
            "detected": self.detected,
            "needs_input": self.needs_input,
            "error": self.error,
        }


def load_from_env(env_path: Optional[Path]) -> tuple[Optional[str], Optional[str]]:
    """Load GIT_USER_NAME and GIT_USER_EMAIL from .env file."""
    name = os.environ.get("GIT_USER_NAME")
    email = os.environ.get("GIT_USER_EMAIL")

    if env_path and env_path.exists():
        content = env_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("GIT_USER_NAME="):
                name = line.split("=", 1)[1].strip("\"'")
            elif line.startswith("GIT_USER_EMAIL="):
                email = line.split("=", 1)[1].strip("\"'")

    return name, email


def detect_from_ssh() -> Optional[str]:
    """Extract GitHub username from SSH authentication."""
    try:
        result = subprocess.run(
            ["ssh", "-T", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # GitHub returns: "Hi username! You've successfully..."
        output = result.stderr
        match = re.search(r"Hi ([^!]+)!", output)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def detect_from_gh() -> tuple[Optional[str], Optional[str]]:
    """Get username and email from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            login = result.stdout.strip()

            # Get email separately
            email_result = subprocess.run(
                ["gh", "api", "user", "-q", ".email"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            email = email_result.stdout.strip()
            if email == "null" or not email:
                email = None

            return login, email
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None, None


def detect_from_git_config() -> tuple[Optional[str], Optional[str]]:
    """Get identity from git config."""
    name = None
    email = None

    try:
        result = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            name = result.stdout.strip()

        result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            email = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return name, email


def derive_noreply_email(username: str) -> str:
    """Derive GitHub noreply email from username."""
    return f"{username}@users.noreply.github.com"


def detect_identity(
    env_path: Optional[Path] = None,
    check_ssh: bool = True,
    check_gh: bool = True,
) -> IdentityResult:
    """
    Detect git identity using cascade:
    1. .env file (GIT_USER_NAME, GIT_USER_EMAIL)
    2. gh CLI user API
    3. SSH authentication to GitHub
    4. git config --global
    """
    result = IdentityResult()

    # 1. Check .env
    name, email = load_from_env(env_path)
    if name and email:
        logger.info("identity_from_env", name=name, email=email)
        result.name = name
        result.email = email
        result.source = "env"
        result.detected = True
        result.exit_code = 0
        return result

    # 2. Check gh CLI (prioritize over SSH since gh is now available)
    if check_gh:
        gh_login, gh_email = detect_from_gh()
        if gh_login:
            logger.info("identity_from_gh", login=gh_login, email=gh_email)
            result.name = gh_login
            result.email = gh_email or derive_noreply_email(gh_login)
            result.source = "gh"
            result.detected = True
            result.needs_input = True  # User should confirm
            result.exit_code = 2
            return result

    # 3. Check SSH
    if check_ssh:
        ssh_username = detect_from_ssh()
        if ssh_username:
            logger.info("identity_from_ssh", username=ssh_username)
            result.name = ssh_username
            result.email = derive_noreply_email(ssh_username)
            result.source = "ssh"
            result.detected = True
            result.needs_input = True  # User should confirm
            result.exit_code = 2
            return result

    # 4. Check git config
    git_name, git_email = detect_from_git_config()
    if git_name and git_email:
        logger.info("identity_from_git_config", name=git_name, email=git_email)
        result.name = git_name
        result.email = git_email
        result.source = "git-config"
        result.detected = True
        result.exit_code = 0
        return result

    # 5. No identity found
    logger.warning("identity_not_found")
    result.needs_input = True
    result.exit_code = 2
    result.error = "No git identity detected"
    return result
