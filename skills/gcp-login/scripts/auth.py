#!/usr/bin/env python3
"""GCP authentication helper script.

Provides programmatic interface to gcloud auth commands.
"""

import os
import re
import subprocess
import sys

from loguru import logger

# Regex patterns for GCP auth URL detection
GCP_URL_PATTERN = re.compile(r"(https://accounts\.google\.com/o/oauth2/auth[^\s]*)")
GCP_ALT_URL_PATTERN = re.compile(r"(https://[\w.-]+\.google\.com/[^\s]*)")


def check_gcloud_installed() -> bool:
    """Check if gcloud CLI is installed.

    Returns:
        True if gcloud is available in PATH
    """
    try:
        result = subprocess.run(
            ["which", "gcloud"],
            capture_output=True,
            text=True
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
            text=True
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
            text=True
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
            text=True
        )
        return result.returncode == 0
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
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to set quota project: {e}")
        return False


def run_gcp_auth(no_browser: bool = True) -> dict:
    """Run gcloud auth login and capture URL for presentation.

    Args:
        no_browser: If True, use device code flow (for containers)

    Returns:
        dict: Result with keys:
            - success: bool
            - auth_url: str | None
            - output: str (full output)
    """
    cmd = ["gcloud", "auth", "login", "--update-adc"]
    if no_browser:
        cmd.append("--no-launch-browser")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    auth_url = None

    for line in process.stdout:
        output_lines.append(line)
        print(line, end='', flush=True)  # Show to user in real-time

        # Detect GCP auth URL
        url_match = GCP_URL_PATTERN.search(line)
        if url_match:
            auth_url = url_match.group(1)
        else:
            # Try alternative URL pattern
            alt_match = GCP_ALT_URL_PATTERN.search(line)
            if alt_match and "oauth" in line.lower():
                auth_url = alt_match.group(1)

    process.wait()

    return {
        "success": process.returncode == 0,
        "auth_url": auth_url,
        "output": "".join(output_lines)
    }


def format_gcp_prompt(auth_url: str) -> str:
    """Format GCP auth URL for user presentation.

    Args:
        auth_url: GCP authentication URL

    Returns:
        str: Formatted markdown table for display
    """
    return f"""
**GCP Authentication Required**

| Field | Value |
|-------|-------|
| URL | {auth_url} |

Open the URL in your browser to authenticate.
"""


def login_with_adc(no_browser: bool = True) -> bool:
    """Run gcloud auth login with ADC update.

    Args:
        no_browser: If True, use device code flow (for containers)

    Returns:
        True if authentication succeeded
    """
    result = run_gcp_auth(no_browser)

    # Present detected auth URL if found
    if result.get("auth_url"):
        logger.info("")
        logger.info(format_gcp_prompt(result["auth_url"]))

    return result["success"]


def main():
    """Main entry point for CLI usage."""
    logger.info("GCP Authentication")

    if not check_gcloud_installed():
        logger.error("gcloud CLI not found. Please install Google Cloud SDK.")
        sys.exit(1)

    # Check current status
    account = get_current_account()
    project = get_current_project()

    if account:
        logger.info(f"Current account: {account}")
    else:
        logger.info("No active account")

    if project:
        logger.info(f"Current project: {project}")
    else:
        logger.info("No project set")

    # Set project from environment if available
    env_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if env_project:
        logger.info(f"Setting project from environment: {env_project}")
        set_project(env_project)
        set_quota_project(env_project)

    # Run authentication
    logger.info("Starting authentication...")
    if login_with_adc():
        logger.success("Authentication successful")

        # Verify
        new_account = get_current_account()
        new_project = get_current_project()
        logger.info(f"Authenticated as: {new_account}")
        logger.info(f"Project: {new_project}")
    else:
        logger.error("Authentication failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
