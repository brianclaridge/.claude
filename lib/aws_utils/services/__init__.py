"""AWS service discovery modules."""

from aws_utils.services.acm import discover_acm_certificates
from aws_utils.services.autoscaling import discover_auto_scaling_groups
from aws_utils.services.cloudwatch import discover_log_groups, discover_alarms
from aws_utils.services.dynamodb import discover_dynamodb_tables
from aws_utils.services.ec2 import (
    discover_ec2_instances,
    discover_elastic_ips,
    discover_internet_gateways,
    discover_internet_gateways_all,
    discover_nat_gateways,
    discover_nat_gateways_all,
    discover_subnets,
    discover_subnets_all,
    discover_vpcs,
)
from aws_utils.services.elb import discover_classic_load_balancers
from aws_utils.services.elbv2 import (
    discover_application_load_balancers,
    discover_network_load_balancers,
)
from aws_utils.services.iam import (
    discover_iam_groups,
    discover_iam_policies,
    discover_iam_roles,
    discover_iam_users,
)
from aws_utils.services.ecs import (
    discover_all_ecs_services,
    discover_ecs_clusters,
    discover_ecs_services,
    discover_ecs_task_definitions,
)
from aws_utils.services.eks import (
    discover_all_eks_fargate_profiles,
    discover_all_eks_node_groups,
    discover_eks_clusters,
    discover_eks_fargate_profiles,
    discover_eks_node_groups,
)
from aws_utils.services.lambda_svc import discover_lambda_functions
from aws_utils.services.organizations import (
    collect_all_accounts,
    discover_organization,
    get_organization_id,
)
from aws_utils.services.rds import discover_rds_clusters, discover_rds_instances
from aws_utils.services.route53 import (
    discover_all_route53_records,
    discover_route53_domains,
    discover_route53_records,
    discover_route53_zones,
)
from aws_utils.services.s3 import discover_s3_buckets
from aws_utils.services.ses import discover_ses_identities
from aws_utils.services.sns import discover_sns_topics
from aws_utils.services.sqs import discover_sqs_queues
from aws_utils.services.sso import (
    DeviceAuthResult,
    discover_account_roles,
    discover_sso_accounts,
    discover_sso_instances,
    poll_for_token,
    start_device_authorization,
)
from aws_utils.services.stepfunctions import (
    discover_sfn_activities,
    discover_state_machines,
)
from aws_utils.services.secrets_manager import discover_secrets
from aws_utils.services.api_gateway import discover_rest_apis, discover_v2_apis
from aws_utils.services.cognito import discover_user_pools, discover_identity_pools
from aws_utils.services.cloudfront import discover_distributions
from aws_utils.services.codebuild import discover_codebuild_projects
from aws_utils.services.codepipeline import discover_pipelines

__all__ = [
    # EC2
    "discover_vpcs",
    "discover_elastic_ips",
    "discover_internet_gateways",
    "discover_internet_gateways_all",
    "discover_nat_gateways",
    "discover_nat_gateways_all",
    "discover_subnets",
    "discover_subnets_all",
    "discover_ec2_instances",
    # IAM
    "discover_iam_roles",
    "discover_iam_policies",
    "discover_iam_users",
    "discover_iam_groups",
    # CloudWatch
    "discover_log_groups",
    "discover_alarms",
    # Load Balancers
    "discover_application_load_balancers",
    "discover_network_load_balancers",
    "discover_classic_load_balancers",
    # Auto Scaling
    "discover_auto_scaling_groups",
    # S3
    "discover_s3_buckets",
    # SQS
    "discover_sqs_queues",
    # SNS
    "discover_sns_topics",
    # SES
    "discover_ses_identities",
    # Organizations
    "discover_organization",
    "get_organization_id",
    "collect_all_accounts",
    # Lambda
    "discover_lambda_functions",
    # RDS
    "discover_rds_instances",
    "discover_rds_clusters",
    # Route53
    "discover_route53_zones",
    "discover_route53_records",
    "discover_all_route53_records",
    "discover_route53_domains",
    # DynamoDB
    "discover_dynamodb_tables",
    # Step Functions
    "discover_state_machines",
    "discover_sfn_activities",
    # SSO
    "discover_sso_instances",
    "discover_sso_accounts",
    "discover_account_roles",
    "start_device_authorization",
    "poll_for_token",
    "DeviceAuthResult",
    # ECS
    "discover_ecs_clusters",
    "discover_ecs_services",
    "discover_all_ecs_services",
    "discover_ecs_task_definitions",
    # EKS
    "discover_eks_clusters",
    "discover_eks_node_groups",
    "discover_all_eks_node_groups",
    "discover_eks_fargate_profiles",
    "discover_all_eks_fargate_profiles",
    # ACM
    "discover_acm_certificates",
    # Secrets Manager
    "discover_secrets",
    # API Gateway
    "discover_rest_apis",
    "discover_v2_apis",
    # Cognito
    "discover_user_pools",
    "discover_identity_pools",
    # CloudFront
    "discover_distributions",
    # CodeBuild
    "discover_codebuild_projects",
    # CodePipeline
    "discover_pipelines",
]
