"""API Gateway discovery (v1 REST and v2 HTTP/WebSocket)."""

from botocore.exceptions import ClientError
from loguru import logger

from ..core.schemas import APIGatewayRestAPI, APIGatewayV2API
from ..core.session import create_session, get_default_region


def discover_rest_apis(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[APIGatewayRestAPI]:
    """Discover API Gateway REST APIs (v1).

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of APIGatewayRestAPI objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("apigateway")

    try:
        apis = []
        paginator = client.get_paginator("get_rest_apis")

        for page in paginator.paginate():
            for api_data in page.get("items", []):
                # Get endpoint type from endpointConfiguration
                endpoint_config = api_data.get("endpointConfiguration", {})
                endpoint_types = endpoint_config.get("types", [])
                endpoint_type = endpoint_types[0] if endpoint_types else "REGIONAL"

                # Format created date
                created = api_data.get("createdDate")

                api = APIGatewayRestAPI(
                    id=api_data.get("id", ""),
                    name=api_data.get("name", ""),
                    description=api_data.get("description"),
                    endpoint_type=endpoint_type,
                    created_date=created.isoformat() if created else None,
                    api_key_source=api_data.get("apiKeySource"),
                    tags=api_data.get("tags", {}),
                    region=region,
                )
                apis.append(api)

        logger.debug(f"Discovered {len(apis)} REST APIs in {region}")
        return apis
    except ClientError as e:
        logger.warning(f"Failed to discover REST APIs: {e}")
        return []


def discover_v2_apis(
    profile_name: str | None = None,
    region: str | None = None,
) -> list[APIGatewayV2API]:
    """Discover API Gateway v2 APIs (HTTP/WebSocket).

    Args:
        profile_name: AWS CLI profile name
        region: AWS region

    Returns:
        List of APIGatewayV2API objects
    """
    region = region or get_default_region()
    session = create_session(profile_name, region)
    client = session.client("apigatewayv2")

    try:
        apis = []
        # Note: apigatewayv2 uses get_apis, no paginator available
        # Use NextToken manually
        params: dict = {}

        while True:
            response = client.get_apis(**params)

            for api_data in response.get("Items", []):
                # Format created date
                created = api_data.get("CreatedDate")

                api = APIGatewayV2API(
                    api_id=api_data.get("ApiId", ""),
                    name=api_data.get("Name", ""),
                    description=api_data.get("Description"),
                    protocol_type=api_data.get("ProtocolType", "HTTP"),
                    api_endpoint=api_data.get("ApiEndpoint"),
                    created_date=created.isoformat() if created else None,
                    tags=api_data.get("Tags", {}),
                    region=region,
                )
                apis.append(api)

            # Check for more pages
            next_token = response.get("NextToken")
            if not next_token:
                break
            params["NextToken"] = next_token

        logger.debug(f"Discovered {len(apis)} HTTP/WebSocket APIs in {region}")
        return apis
    except ClientError as e:
        logger.warning(f"Failed to discover v2 APIs: {e}")
        return []
