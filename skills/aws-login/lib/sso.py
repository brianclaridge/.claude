"""AWS SSO login operations."""

import re
import subprocess
from dataclasses import dataclass

from loguru import logger

# Regex patterns for SSO URL and device code detection
SSO_URL_PATTERN = re.compile(r"(https://[\w.-]+\.awsapps\.com/start[^\s]*)")
DEVICE_CODE_PATTERN = re.compile(r"\b([A-Z]{4}-[A-Z]{4})\b")


@dataclass
class SSOResult:
    """Result of SSO login attempt."""

    success: bool
    sso_url: str | None = None
    device_code: str | None = None
    output: str = ""
    error: str | None = None


def check_credentials_valid(profile_name: str) -> bool:
    """Check if SSO credentials are currently valid.

    Args:
        profile_name: AWS CLI profile name

    Returns:
        True if credentials are valid
    """
    logger.debug(f"Checking credentials for profile: {profile_name}")

    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--profile", profile_name],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        logger.debug("Credentials valid")
        return True

    logger.debug(f"Credentials invalid: {result.stderr.strip()}")
    return False


def run_sso_login(profile_name: str, no_browser: bool = True) -> SSOResult:
    """Run AWS SSO login and capture URL/device code.

    Args:
        profile_name: AWS CLI profile name
        no_browser: If True, use device code flow

    Returns:
        SSOResult with success status and captured URL/code
    """
    cmd = ["aws", "sso", "login", "--profile", profile_name]
    if no_browser:
        cmd.append("--no-browser")

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
        sso_url = None
        device_code = None

        url_shown = False

        for line in process.stdout:
            output_lines.append(line)

            # Detect SSO URL
            url_match = SSO_URL_PATTERN.search(line)
            if url_match:
                sso_url = url_match.group(1)

            # Detect device code (XXXX-XXXX pattern)
            code_match = DEVICE_CODE_PATTERN.search(line)
            if code_match:
                device_code = code_match.group(1)

            # Show formatted table as soon as we have both URL and code
            if sso_url and device_code and not url_shown:
                url_shown = True
                # Append user_code to URL if not already present
                display_url = sso_url
                if "user_code=" not in sso_url:
                    separator = "&" if "?" in sso_url else "?"
                    display_url = f"{sso_url}{separator}user_code={device_code}"
                print(f"\n| Field | Value |")
                print(f"|-------|-------|")
                print(f"| URL   | {display_url} |")
                print(f"| Code  | {device_code} |")
                print(f"\nOpen URL in browser and enter code to authenticate.\n", flush=True)

        process.wait()

        return SSOResult(
            success=process.returncode == 0,
            sso_url=sso_url,
            device_code=device_code,
            output="".join(output_lines),
        )

    except KeyboardInterrupt:
        if process:
            process.terminate()
        raise  # Re-raise to let caller handle graceful exit
    except Exception as e:
        logger.error(f"SSO login failed: {e}")
        return SSOResult(success=False, error=str(e))


def format_sso_prompt(result: SSOResult) -> str:
    """Format SSO URL and device code for display.

    Args:
        result: SSOResult with URL and code

    Returns:
        Formatted markdown string
    """
    if not result.sso_url:
        return ""

    lines = [
        "",
        "**AWS SSO Authentication Required**",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| URL | {result.sso_url} |",
    ]

    if result.device_code:
        lines.append(f"| Code | {result.device_code} |")

    lines.extend([
        "",
        "Open the URL in your browser to authenticate.",
        "",
    ])

    return "\n".join(lines)
