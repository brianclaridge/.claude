"""ACM certificate discovery."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import ACMCertificate
from ..core.session import create_session


def discover_acm_certificates(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[ACMCertificate]:
    """Discover all ACM certificates in a region.

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of ACMCertificate objects
    """
    session = create_session(profile_name, region)
    acm_client = session.client("acm")
    region_name = session.region_name or "us-east-1"

    try:
        certificates = []
        paginator = acm_client.get_paginator("list_certificates")

        cert_arns = []
        for page in paginator.paginate():
            for cert_summary in page.get("CertificateSummaryList", []):
                cert_arns.append(cert_summary["CertificateArn"])

        # Describe each certificate for full details
        for arn in cert_arns:
            response = acm_client.describe_certificate(CertificateArn=arn)
            cert_data = response.get("Certificate", {})

            certificate = ACMCertificate(
                certificate_arn=cert_data.get("CertificateArn", arn),
                domain_name=cert_data.get("DomainName", ""),
                status=cert_data.get("Status", "UNKNOWN"),
                certificate_type=cert_data.get("Type", "UNKNOWN"),
                issuer=cert_data.get("Issuer"),
                not_before=cert_data.get("NotBefore"),
                not_after=cert_data.get("NotAfter"),
                in_use_by=cert_data.get("InUseBy", []),
                subject_alternative_names=cert_data.get("SubjectAlternativeNames", []),
                region=region_name,
            )
            certificates.append(certificate)

        logger.debug(f"Discovered {len(certificates)} ACM certificates in {region_name}")
        return certificates
    except ClientError as e:
        logger.warning(f"Failed to discover ACM certificates: {e}")
        return []
