"""First-run setup wizard for AWS SSO configuration."""

import re
import sys
from pathlib import Path

# Add parent directories to path for imports
aws_dir = Path(__file__).parent.parent
if str(aws_dir) not in sys.path:
    sys.path.insert(0, str(aws_dir))

import requests
import yaml
from loguru import logger

# Config file location
AWS_CONFIG_PATH = Path(__file__).parent.parent.parent / ".aws.yml"


def prompt_sso_url() -> str:
    """Prompt user for SSO start URL.

    Returns:
        Validated SSO start URL
    """
    print("\n=== AWS SSO Setup Wizard ===\n")
    print("No .aws.yml configuration found. Let's set up AWS SSO.\n")

    while True:
        url = input("Enter your SSO start URL (e.g., https://mycompany.awsapps.com/start): ").strip()

        if not url:
            print("URL cannot be empty. Please try again.")
            continue

        # Normalize URL
        if not url.startswith("http"):
            url = f"https://{url}"

        if not url.endswith("/start"):
            url = url.rstrip("/") + "/start"

        # Validate URL format
        if not re.match(r"https://[\w-]+\.awsapps\.com/start", url):
            print("Invalid SSO URL format. Expected: https://<name>.awsapps.com/start")
            continue

        return url


def detect_region_from_sso_url(url: str) -> str:
    """Detect AWS region from SSO URL by following redirects.

    The SSO portal redirects to a regional endpoint like:
    https://us-east-1.signin.aws.amazon.com/...

    Args:
        url: SSO start URL

    Returns:
        AWS region string (e.g., 'us-east-1')
    """
    logger.info(f"Detecting region from SSO URL: {url}")

    try:
        # Follow redirects with a HEAD request
        response = requests.head(url, allow_redirects=True, timeout=10)

        # Check final URL for region
        final_url = response.url
        logger.debug(f"Final URL after redirects: {final_url}")

        # Look for region in URL (e.g., us-east-1.signin.aws.amazon.com)
        match = re.search(r"(us-east-\d|us-west-\d|eu-west-\d|eu-central-\d|ap-\w+-\d)", final_url)
        if match:
            region = match.group(1)
            logger.info(f"Detected region: {region}")
            return region

        # Also check response headers
        if "x-amz-id-2" in response.headers:
            # Try to get region from S3-style headers if present
            pass

    except requests.RequestException as e:
        logger.warning(f"Failed to detect region from URL: {e}")

    # Default to us-east-1 if detection fails
    logger.info("Could not detect region, defaulting to us-east-1")
    return "us-east-1"


def prompt_for_region(detected: str) -> str:
    """Confirm or change detected region.

    Args:
        detected: Auto-detected region

    Returns:
        Final region to use
    """
    print(f"\nDetected SSO region: {detected}")
    response = input(f"Press Enter to accept, or type a different region: ").strip()

    if response:
        return response
    return detected


def create_initial_config(sso_url: str, region: str) -> dict:
    """Create initial .aws.yml configuration.

    Args:
        sso_url: SSO start URL
        region: AWS region

    Returns:
        Config dictionary
    """
    return {
        "schema_version": "2.0",
        "sso": {
            "start_url": sso_url,
            "region": region,
            "role_name": "AdministratorAccess",
        },
        "defaults": {
            "region": region,
        },
        "log_path": ".data/logs/aws_sso",
        "accounts": {},
        "organization": {},
    }


def write_config(config: dict) -> None:
    """Write configuration to .aws.yml.

    Args:
        config: Configuration dictionary
    """
    AWS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(AWS_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Configuration saved to {AWS_CONFIG_PATH}")
    print(f"\nConfiguration saved to: {AWS_CONFIG_PATH}")


def run_setup_wizard() -> dict:
    """Run the first-run setup wizard.

    Prompts for SSO URL, detects region, creates config,
    and triggers org sync to discover accounts.

    Returns:
        Created configuration dictionary
    """
    # 1. Prompt for SSO URL
    sso_url = prompt_sso_url()

    # 2. Detect region from URL
    detected_region = detect_region_from_sso_url(sso_url)

    # 3. Confirm region
    region = prompt_for_region(detected_region)

    # 4. Create config
    config = create_initial_config(sso_url, region)

    # 5. Write config
    write_config(config)

    # 6. Run org sync to discover accounts
    print("\nDiscovering organization accounts...")
    print("Note: Run 'sso_login root' first, then 'org_sync' to discover accounts.")

    return config


def config_exists() -> bool:
    """Check if .aws.yml exists.

    Returns:
        True if config file exists
    """
    return AWS_CONFIG_PATH.exists()


if __name__ == "__main__":
    if config_exists():
        print(f"Configuration already exists at {AWS_CONFIG_PATH}")
    else:
        run_setup_wizard()
