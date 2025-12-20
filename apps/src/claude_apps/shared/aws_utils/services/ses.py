"""SES identity discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import SESIdentity
from ..core.session import create_session, get_default_region


def discover_ses_identities(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[SESIdentity]:
    """Discover all SES identities (emails and domains) in an account/region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of SESIdentity objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    ses = session.client("ses")

    try:
        identities = []

        # List all identities
        response = ses.list_identities()
        identity_names = response.get("Identities", [])

        if not identity_names:
            logger.debug(f"No SES identities found in {region}")
            return []

        # Get verification status for all identities
        try:
            attrs_response = ses.get_identity_verification_attributes(
                Identities=identity_names
            )
            verification_attrs = attrs_response.get("VerificationAttributes", {})
        except ClientError:
            verification_attrs = {}

        for identity_name in identity_names:
            # Determine type (email vs domain)
            identity_type = "EmailAddress" if "@" in identity_name else "Domain"

            # Get verification status
            attrs = verification_attrs.get(identity_name, {})
            verification_status = attrs.get("VerificationStatus", "Unknown")

            identity = SESIdentity(
                identity=identity_name,
                type=identity_type,
                verification_status=verification_status,
                region=region,
            )
            identities.append(identity)

        logger.debug(f"Discovered {len(identities)} SES identities in {region}")
        return identities
    except ClientError as e:
        logger.warning(f"Failed to discover SES identities: {e}")
        return []
