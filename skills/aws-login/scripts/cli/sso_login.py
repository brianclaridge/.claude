#!/usr/bin/env python3
"""
AWS SSO login handler.

Initiates AWS SSO login flow for specified account.
Supports interactive account selection when no account specified.
"""

import argparse
import re
import sys
from pathlib import Path
import subprocess

# Regex patterns for SSO URL and device code detection
SSO_URL_PATTERN = re.compile(r"(https://[\w.-]+\.awsapps\.com/start[^\s]*)")
DEVICE_CODE_PATTERN = re.compile(r"\b([A-Z]{4}-[A-Z]{4})\b")

# Add parent directories to path for imports
aws_dir = Path(__file__).parent.parent
if str(aws_dir) not in sys.path:
    sys.path.insert(0, str(aws_dir))

from loguru import logger

from core.logging_config import setup_logging
from core.config_reader import get_account_by_alias, get_profile_name, get_sso_start_url, list_all_accounts
from config.aws_config_helper import ensure_profile_for_account


def find_alias_for_account_id(account_id: str) -> str | None:
    """
    Find configured alias for an account ID.

    Args:
        account_id: AWS account ID (12 digits)

    Returns:
        str: Alias if found in aws.yml, None otherwise
    """
    for acc in list_all_accounts():
        if str(acc.get('account_number')) == account_id:
            return acc.get('alias')
    return None


def check_credentials_valid(profile_name: str) -> bool:
    """
    Check if SSO credentials are currently valid for the profile.

    Args:
        profile_name: AWS profile name

    Returns:
        bool: True if credentials valid, False if expired/missing
    """
    logger.debug(f"Checking credential validity for profile: {profile_name}")

    result = subprocess.run(
        ['aws', 'sts', 'get-caller-identity', '--profile', profile_name],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        logger.debug("Credentials are valid")
        return True
    else:
        logger.debug(f"Credentials invalid or expired: {result.stderr.strip()}")
        return False


def run_sso_login(profile_name: str) -> dict:
    """
    Run AWS SSO login and capture URL/device code for presentation.

    Args:
        profile_name: AWS CLI profile name

    Returns:
        dict: Result with keys:
            - success: bool
            - sso_url: str | None
            - device_code: str | None
            - output: str (full output)
    """
    process = subprocess.Popen(
        ['aws', 'sso', 'login', '--profile', profile_name, '--no-browser'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    sso_url = None
    device_code = None

    for line in process.stdout:
        output_lines.append(line)
        print(line, end='', flush=True)  # Show to user in real-time

        # Detect SSO URL
        url_match = SSO_URL_PATTERN.search(line)
        if url_match:
            sso_url = url_match.group(1)

        # Detect device code (4 letters - 4 letters pattern)
        code_match = DEVICE_CODE_PATTERN.search(line)
        if code_match:
            device_code = code_match.group(1)

    process.wait()

    return {
        "success": process.returncode == 0,
        "sso_url": sso_url,
        "device_code": device_code,
        "output": "".join(output_lines)
    }


def format_sso_prompt(sso_url: str, device_code: str) -> str:
    """
    Format SSO URL and device code for user presentation.

    Args:
        sso_url: AWS SSO URL
        device_code: Device verification code

    Returns:
        str: Formatted markdown table for display
    """
    return f"""
**AWS SSO Authentication Required**

| Field | Value |
|-------|-------|
| URL | {sso_url} |
| Code | **{device_code}** |

Open the URL in your browser and enter the code to authenticate.
"""


def main() -> int:
    """
    Main execution function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description='AWS SSO login handler',
        epilog='Example: sso_login.py root --force'
    )
    parser.add_argument('account_alias', nargs='?', default=None,
                       help='Account alias from aws.yml (interactive menu if omitted)')
    parser.add_argument('--force', action='store_true',
                       help='Force login even if credentials are currently valid')
    parser.add_argument('--export', action='store_true',
                       help='Output export AWS_PROFILE statement for shell eval')
    args = parser.parse_args()

    # Setup logging after parsing args (suppress for --export mode)
    if not args.export:
        setup_logging("sso_login")

    export_mode = args.export

    # Track dynamic account (not in aws.yml)
    dynamic_account = None

    # If no account specified, show interactive menu
    if not args.account_alias:
        from discovery.account_discovery import get_org_accounts, show_account_menu

        try:
            logger.info("No account specified - launching interactive selection...")
            logger.info("")

            accounts = get_org_accounts()
            selected = show_account_menu(accounts)

            if selected is None:
                logger.info("Selection cancelled")
                return 0

            # Map to alias or use account name
            account_alias = find_alias_for_account_id(selected['Id'])
            if not account_alias:
                # Dynamic account - not in aws.yml, use selected data directly
                account_alias = selected['Name'].lower().replace(' ', '-').replace('_', '-')
                dynamic_account = {
                    'account_name': selected['Name'],
                    'account_number': selected['Id'],
                }
                logger.info(f"Using dynamic account: {selected['Name']} ({selected['Id']})")

        except Exception as e:
            logger.error(f"Failed to discover accounts: {e}")
            logger.error("Hint: Ensure 'root' account credentials are valid")
            logger.error("  Run: task sso:login ACCOUNT=root")
            return 1
    else:
        account_alias = args.account_alias

    def log_info(msg: str) -> None:
        if not export_mode:
            logger.info(msg)

    def log_success(msg: str) -> None:
        if not export_mode:
            logger.success(msg)

    def log_error(msg: str) -> None:
        if export_mode:
            print(msg, file=sys.stderr)
        else:
            logger.error(msg)

    def output_export(profile: str) -> None:
        if export_mode:
            print(f"export AWS_PROFILE={profile}")

    try:
        # Get account data - either from config or dynamic selection
        if dynamic_account:
            account = dynamic_account
            profile_name = account_alias
        else:
            account = get_account_by_alias(account_alias)
            profile_name = get_profile_name(account_alias)

        sso_url = get_sso_start_url()

        log_info("AWS SSO Login")
        log_info(f"  Account: {account_alias}")
        log_info(f"  Name: {account.get('account_name', account_alias)}")
        log_info(f"  Number: {account['account_number']}")
        log_info(f"  Profile: {profile_name}")
        if sso_url:
            log_info(f"  SSO URL: {sso_url}")
        log_info("")

        # Ensure AWS profile exists (auto-create if missing)
        if dynamic_account:
            # For dynamic accounts, create profile directly
            from config.aws_config_helper import ensure_profile_exists, set_default_profile
            from core.config_reader import get_default_region

            region = get_default_region()
            ensure_profile_exists(account_alias, account, region, sso_url)
            set_default_profile(account_alias, account, region, sso_url)
        else:
            ensure_profile_for_account(account_alias)

        # Check if credentials already valid (unless --force flag used)
        if not args.force and check_credentials_valid(profile_name):
            log_success(f"Credentials already valid for: {account_alias}")
            log_info(f"  Profile: {profile_name}")
            log_info("  Default profile updated - AWS CLI commands will use this account")
            log_info("")
            log_info(f"  To force re-login: uv run scripts/sso_login.py {account_alias} --force")
            output_export(profile_name)
            return 0

        # Credentials expired/missing - proceed with login
        if args.force:
            log_info("Force flag enabled - proceeding with login")
        else:
            log_info("Credentials expired or missing - initiating login")

        log_info("Initiating AWS SSO login (no-browser mode)...")
        log_info("")

        # Execute AWS SSO login with output capture for URL/code detection
        result = run_sso_login(profile_name)

        # Present detected SSO URL and code if found
        if result.get("sso_url") and result.get("device_code"):
            log_info("")
            log_info(format_sso_prompt(result["sso_url"], result["device_code"]))

        if result["success"]:
            log_success("SSO login successful")
            log_info(f"Credentials cached for profile: {profile_name}")
            log_info("Default profile updated - AWS CLI commands will use this account")
            output_export(profile_name)
            return 0
        else:
            log_error("SSO login failed")
            return 1

    except ValueError as e:
        log_error(str(e))
        return 1
    except FileNotFoundError as e:
        log_error(f"Configuration file not found: {e}")
        return 1
    except Exception as e:
        if export_mode:
            print(f"Unexpected error: {e}", file=sys.stderr)
        else:
            logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
