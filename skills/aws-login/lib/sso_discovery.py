"""AWS SSO OIDC device authorization flow for account discovery.

Enables bootstrapping without pre-configured AWS CLI profiles by using
the SSO OIDC device authorization grant to discover available accounts.
"""

import time
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError
from loguru import logger


@dataclass
class DeviceAuthResult:
    """Result of device authorization flow."""

    success: bool
    access_token: str | None = None
    verification_uri: str | None = None
    user_code: str | None = None
    error: str | None = None


@dataclass
class DiscoveredAccount:
    """Account discovered via SSO."""

    account_id: str
    account_name: str
    email: str


def start_device_authorization(
    sso_start_url: str,
    region: str = "us-east-1",
) -> DeviceAuthResult:
    """Start SSO OIDC device authorization flow.

    This initiates the device code flow and returns the verification
    URI and user code for the user to complete authentication.

    Args:
        sso_start_url: AWS SSO start URL (e.g., https://org.awsapps.com/start)
        region: AWS region for SSO

    Returns:
        DeviceAuthResult with verification URI and user code
    """
    try:
        sso_oidc = boto3.client("sso-oidc", region_name=region)

        # Step 1: Register a temporary public client
        logger.debug("Registering SSO OIDC client...")
        client_response = sso_oidc.register_client(
            clientName="aws-login-discovery",
            clientType="public",
        )
        client_id = client_response["clientId"]
        client_secret = client_response["clientSecret"]

        # Step 2: Start device authorization
        logger.debug("Starting device authorization...")
        auth_response = sso_oidc.start_device_authorization(
            clientId=client_id,
            clientSecret=client_secret,
            startUrl=sso_start_url,
        )

        return DeviceAuthResult(
            success=True,
            verification_uri=auth_response["verificationUriComplete"],
            user_code=auth_response["userCode"],
        )

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Device authorization failed: {error_msg}")
        return DeviceAuthResult(success=False, error=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error in device authorization: {e}")
        return DeviceAuthResult(success=False, error=str(e))


def poll_for_token(
    sso_start_url: str,
    region: str = "us-east-1",
    timeout_seconds: int = 300,
    poll_interval: int = 5,
) -> DeviceAuthResult:
    """Complete device authorization by polling for user approval.

    This function handles the full device auth flow:
    1. Registers a client
    2. Starts device authorization
    3. Displays verification info
    4. Polls until user approves or timeout

    Args:
        sso_start_url: AWS SSO start URL
        region: AWS region for SSO
        timeout_seconds: Max time to wait for approval (default 5 min)
        poll_interval: Seconds between poll attempts

    Returns:
        DeviceAuthResult with access token if successful
    """
    try:
        sso_oidc = boto3.client("sso-oidc", region_name=region)

        # Register client
        logger.debug("Registering SSO OIDC client...")
        client_response = sso_oidc.register_client(
            clientName="aws-login-discovery",
            clientType="public",
        )
        client_id = client_response["clientId"]
        client_secret = client_response["clientSecret"]

        # Start device authorization
        logger.debug("Starting device authorization...")
        auth_response = sso_oidc.start_device_authorization(
            clientId=client_id,
            clientSecret=client_secret,
            startUrl=sso_start_url,
        )

        device_code = auth_response["deviceCode"]
        verification_uri = auth_response["verificationUriComplete"]
        user_code = auth_response["userCode"]
        interval = auth_response.get("interval", poll_interval)

        # Display verification info
        print(f"\n| Field | Value |")
        print(f"|-------|-------|")
        print(f"| URL   | {verification_uri} |")
        print(f"| Code  | {user_code} |")
        print(f"\nOpen URL in browser and enter code to authenticate.\n", flush=True)

        # Poll for token
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                token_response = sso_oidc.create_token(
                    clientId=client_id,
                    clientSecret=client_secret,
                    grantType="urn:ietf:params:oauth:grant-type:device_code",
                    deviceCode=device_code,
                )

                logger.debug("Device authorization approved")
                return DeviceAuthResult(
                    success=True,
                    access_token=token_response["accessToken"],
                    verification_uri=verification_uri,
                    user_code=user_code,
                )

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                if error_code == "AuthorizationPendingException":
                    # User hasn't approved yet, continue polling
                    time.sleep(interval)
                    continue
                elif error_code == "SlowDownException":
                    # Too fast, increase interval
                    interval += 5
                    time.sleep(interval)
                    continue
                elif error_code == "ExpiredTokenException":
                    return DeviceAuthResult(
                        success=False,
                        error="Device code expired. Please try again.",
                    )
                else:
                    return DeviceAuthResult(
                        success=False,
                        error=f"Token creation failed: {error_code}",
                    )

        return DeviceAuthResult(
            success=False,
            error=f"Timeout after {timeout_seconds} seconds waiting for approval",
        )

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Device authorization failed: {error_msg}")
        return DeviceAuthResult(success=False, error=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return DeviceAuthResult(success=False, error=str(e))


def discover_available_accounts(
    access_token: str,
    region: str = "us-east-1",
) -> list[DiscoveredAccount]:
    """List all accounts available to the authenticated user.

    Args:
        access_token: SSO access token from device authorization
        region: AWS region for SSO

    Returns:
        List of DiscoveredAccount objects
    """
    try:
        sso = boto3.client("sso", region_name=region)

        accounts = []
        paginator_params = {"accessToken": access_token, "maxResults": 100}

        while True:
            response = sso.list_accounts(**paginator_params)

            for account in response.get("accountList", []):
                accounts.append(
                    DiscoveredAccount(
                        account_id=account["accountId"],
                        account_name=account.get("accountName", ""),
                        email=account.get("emailAddress", ""),
                    )
                )

            next_token = response.get("nextToken")
            if not next_token:
                break
            paginator_params["nextToken"] = next_token

        logger.debug(f"Discovered {len(accounts)} accounts via SSO")
        return accounts

    except ClientError as e:
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Failed to list accounts: {error_msg}")
        return []


def discover_account_roles(
    access_token: str,
    account_id: str,
    region: str = "us-east-1",
) -> list[str]:
    """List available roles for an account.

    Args:
        access_token: SSO access token
        account_id: AWS account ID
        region: AWS region for SSO

    Returns:
        List of role names available in the account
    """
    try:
        sso = boto3.client("sso", region_name=region)

        roles = []
        paginator_params = {
            "accessToken": access_token,
            "accountId": account_id,
            "maxResults": 100,
        }

        while True:
            response = sso.list_account_roles(**paginator_params)

            for role in response.get("roleList", []):
                roles.append(role["roleName"])

            next_token = response.get("nextToken")
            if not next_token:
                break
            paginator_params["nextToken"] = next_token

        return roles

    except ClientError as e:
        logger.warning(f"Failed to list roles for {account_id}: {e}")
        return []
