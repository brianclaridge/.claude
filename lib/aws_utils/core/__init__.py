"""Core module - session management and schemas."""

from aws_utils.core.schemas import (
    VPC,
    AccountInventory,
    ElasticIP,
    InternetGateway,
    NATGateway,
    S3Bucket,
    SESIdentity,
    SNSTopic,
    SQSQueue,
    Subnet,
)
from aws_utils.core.session import create_session, get_default_region

__all__ = [
    "create_session",
    "get_default_region",
    "AccountInventory",
    "VPC",
    "Subnet",
    "InternetGateway",
    "NATGateway",
    "ElasticIP",
    "S3Bucket",
    "SQSQueue",
    "SNSTopic",
    "SESIdentity",
]
