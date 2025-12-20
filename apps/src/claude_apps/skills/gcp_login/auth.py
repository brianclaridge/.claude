"""GCP authentication operations."""

import os
import re
import subprocess
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

# Regex patterns for GCP auth URL detection
GCP_URL_PATTERN = re.compile(r"(https://accounts\.google\.com/o/oauth2/auth[^\s]*)")
GCP_ALT_URL_PATTERN = re.compile(r"(https://[\w.-]+\.google\.com/[^\s]*)")


@dataclass
class AuthResult:
    """Result of GCP auth attempt."""

    success: bool
    auth_url: str | None = None
    output: str = ""
    error: str | None = None


def check_gcloud_installed() -> bool:
    """Check if gcloud CLI is installed."""
    try:
        result = subprocess.run(
            ["which", "gcloud"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_current_account() -> str | None:
    """Get currently authenticated account.

    Returns:
        Account email or None if not authenticated
    """
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except Exception:
        return None


def get_current_project() -> str | None:
    """Get currently configured project.

    Returns:
        Project ID or None if not set
    """
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            project = result.stdout.strip()
            if project != "(unset)":
                return project
        return None
    except Exception:
        return None


def set_project(project_id: str) -> bool:
    """Set the active GCP project.

    Args:
        project_id: GCP project ID

    Returns:
        True if successful
    """
    try:
        result = subprocess.run(
            ["gcloud", "config", "set", "project", project_id],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.debug(f"Set project: {project_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to set project: {e}")
        return False


def set_quota_project(project_id: str) -> bool:
    """Set the quota project for ADC.

    Args:
        project_id: GCP project ID for quota

    Returns:
        True if successful
    """
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "set-quota-project", project_id],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to set quota project: {e}")
        return False


def run_auth(no_browser: bool = True) -> AuthResult:
    """Run gcloud auth login and capture URL.

    Args:
        no_browser: If True, use device code flow

    Returns:
        AuthResult with success status and captured URL
    """
    cmd = ["gcloud", "auth", "login", "--update-adc"]
    if no_browser:
        cmd.append("--no-launch-browser")

    logger.debug(f"Running: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines = []
        auth_url = None

        for line in process.stdout:
            output_lines.append(line)
            print(line, end="", flush=True)

            # Detect GCP auth URL
            url_match = GCP_URL_PATTERN.search(line)
            if url_match:
                auth_url = url_match.group(1)
            else:
                alt_match = GCP_ALT_URL_PATTERN.search(line)
                if alt_match and "oauth" in line.lower():
                    auth_url = alt_match.group(1)

        process.wait()

        return AuthResult(
            success=process.returncode == 0,
            auth_url=auth_url,
            output="".join(output_lines),
        )

    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return AuthResult(success=False, error=str(e))


def format_auth_prompt(result: AuthResult) -> str:
    """Format auth URL for display.

    Args:
        result: AuthResult with URL

    Returns:
        Formatted markdown string
    """
    if not result.auth_url:
        return ""

    return f"""
**GCP Authentication Required**

| Field | Value |
|-------|-------|
| URL | {result.auth_url} |

Open the URL in your browser to authenticate.
"""
