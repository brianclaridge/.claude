"""Tests for new AWS service discovery modules."""

from unittest.mock import MagicMock, patch

import pytest

from aws_utils.core.schemas import (
    AccountInventory,
    DynamoDBTable,
    LambdaFunction,
    RDSCluster,
    RDSInstance,
    Route53Record,
    Route53Zone,
    SFNActivity,
    SSOAccount,
    SSOInstance,
    StateMachine,
)


class TestSchemas:
    """Test new Pydantic schema models."""

    def test_lambda_function_schema(self):
        """Test LambdaFunction schema instantiation."""
        func = LambdaFunction(
            function_name="test-function",
            runtime="python3.12",
            memory_size=128,
            timeout=30,
            last_modified="2024-01-01T00:00:00Z",
            arn="arn:aws:lambda:us-east-1:123456789:function:test-function",
            region="us-east-1",
        )
        assert func.function_name == "test-function"
        assert func.runtime == "python3.12"
        assert func.memory_size == 128

    def test_lambda_function_optional_runtime(self):
        """Test LambdaFunction with None runtime (container image)."""
        func = LambdaFunction(
            function_name="container-func",
            runtime=None,
            memory_size=512,
            timeout=60,
            last_modified="2024-01-01T00:00:00Z",
            arn="arn:aws:lambda:us-east-1:123456789:function:container-func",
            region="us-east-1",
        )
        assert func.runtime is None

    def test_rds_instance_schema(self):
        """Test RDSInstance schema instantiation."""
        instance = RDSInstance(
            db_instance_identifier="test-db",
            engine="mysql",
            engine_version="8.0.35",
            instance_class="db.t3.micro",
            status="available",
            endpoint="test-db.123456789.us-east-1.rds.amazonaws.com",
            port=3306,
            arn="arn:aws:rds:us-east-1:123456789:db:test-db",
            region="us-east-1",
        )
        assert instance.db_instance_identifier == "test-db"
        assert instance.engine == "mysql"
        assert instance.status == "available"

    def test_rds_cluster_schema(self):
        """Test RDSCluster schema instantiation."""
        cluster = RDSCluster(
            cluster_identifier="test-cluster",
            engine="aurora-postgresql",
            engine_version="15.4",
            status="available",
            endpoint="test-cluster.cluster-123456789.us-east-1.rds.amazonaws.com",
            reader_endpoint="test-cluster.cluster-ro-123456789.us-east-1.rds.amazonaws.com",
            port=5432,
            arn="arn:aws:rds:us-east-1:123456789:cluster:test-cluster",
            region="us-east-1",
        )
        assert cluster.cluster_identifier == "test-cluster"
        assert cluster.engine == "aurora-postgresql"

    def test_route53_zone_schema(self):
        """Test Route53Zone schema instantiation."""
        zone = Route53Zone(
            zone_id="Z1234567890ABC",
            name="example.com.",
            is_private=False,
            record_count=10,
        )
        assert zone.zone_id == "Z1234567890ABC"
        assert zone.name == "example.com."
        assert not zone.is_private

    def test_route53_record_schema(self):
        """Test Route53Record schema instantiation."""
        record = Route53Record(
            zone_id="Z1234567890ABC",
            name="www.example.com.",
            record_type="A",
            ttl=300,
            values=["192.0.2.1"],
        )
        assert record.name == "www.example.com."
        assert record.record_type == "A"
        assert record.ttl == 300

    def test_route53_record_alias(self):
        """Test Route53Record with alias (no TTL)."""
        record = Route53Record(
            zone_id="Z1234567890ABC",
            name="app.example.com.",
            record_type="A",
            ttl=None,
            values=["ALIAS dualstack.elb.amazonaws.com"],
        )
        assert record.ttl is None

    def test_dynamodb_table_schema(self):
        """Test DynamoDBTable schema instantiation."""
        table = DynamoDBTable(
            table_name="test-table",
            status="ACTIVE",
            item_count=1000,
            size_bytes=102400,
            arn="arn:aws:dynamodb:us-east-1:123456789:table/test-table",
            region="us-east-1",
        )
        assert table.table_name == "test-table"
        assert table.status == "ACTIVE"
        assert table.item_count == 1000

    def test_state_machine_schema(self):
        """Test StateMachine schema instantiation."""
        sm = StateMachine(
            name="test-state-machine",
            arn="arn:aws:states:us-east-1:123456789:stateMachine:test-state-machine",
            status="ACTIVE",
            machine_type="STANDARD",
            creation_date="2024-01-01T00:00:00Z",
            region="us-east-1",
        )
        assert sm.name == "test-state-machine"
        assert sm.machine_type == "STANDARD"

    def test_sfn_activity_schema(self):
        """Test SFNActivity schema instantiation."""
        activity = SFNActivity(
            name="test-activity",
            arn="arn:aws:states:us-east-1:123456789:activity:test-activity",
            creation_date="2024-01-01T00:00:00Z",
            region="us-east-1",
        )
        assert activity.name == "test-activity"

    def test_sso_instance_schema(self):
        """Test SSOInstance schema instantiation."""
        instance = SSOInstance(
            instance_arn="arn:aws:sso:::instance/ssoins-1234567890abcdef",
            identity_store_id="d-1234567890",
        )
        assert instance.identity_store_id == "d-1234567890"

    def test_sso_account_schema(self):
        """Test SSOAccount schema instantiation."""
        account = SSOAccount(
            account_id="123456789012",
            account_name="sandbox",
            email_address="sandbox@example.com",
        )
        assert account.account_id == "123456789012"
        assert account.account_name == "sandbox"

    def test_account_inventory_with_new_fields(self):
        """Test AccountInventory includes new resource fields."""
        inventory = AccountInventory(
            account_id="123456789012",
            account_alias="sandbox",
            region="us-east-1",
            lambda_functions=[
                LambdaFunction(
                    function_name="test",
                    runtime="python3.12",
                    memory_size=128,
                    timeout=30,
                    last_modified="2024-01-01T00:00:00Z",
                    arn="arn:aws:lambda:us-east-1:123456789:function:test",
                    region="us-east-1",
                )
            ],
            rds_instances=[],
            rds_clusters=[],
            route53_zones=[],
            dynamodb_tables=[],
            state_machines=[],
            sfn_activities=[],
        )
        assert len(inventory.lambda_functions) == 1
        assert inventory.lambda_functions[0].function_name == "test"


class TestServiceDiscoveryFunctions:
    """Test service discovery functions with mocked boto3."""

    @patch("aws_utils.services.lambda_svc.create_session")
    def test_discover_lambda_functions_empty(self, mock_session):
        """Test Lambda discovery with empty response."""
        from aws_utils.services.lambda_svc import discover_lambda_functions

        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Functions": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_client
        mock_session.return_value.region_name = "us-east-1"

        result = discover_lambda_functions()
        assert result == []

    @patch("aws_utils.services.rds.create_session")
    def test_discover_rds_instances_empty(self, mock_session):
        """Test RDS instance discovery with empty response."""
        from aws_utils.services.rds import discover_rds_instances

        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"DBInstances": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_client
        mock_session.return_value.region_name = "us-east-1"

        result = discover_rds_instances()
        assert result == []

    @patch("aws_utils.services.route53.create_session")
    def test_discover_route53_zones_empty(self, mock_session):
        """Test Route53 zone discovery with empty response."""
        from aws_utils.services.route53 import discover_route53_zones

        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"HostedZones": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_client

        result = discover_route53_zones()
        assert result == []

    @patch("aws_utils.services.dynamodb.create_session")
    def test_discover_dynamodb_tables_empty(self, mock_session):
        """Test DynamoDB table discovery with empty response."""
        from aws_utils.services.dynamodb import discover_dynamodb_tables

        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"TableNames": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_client
        mock_session.return_value.region_name = "us-east-1"

        result = discover_dynamodb_tables()
        assert result == []

    @patch("aws_utils.services.stepfunctions.create_session")
    def test_discover_state_machines_empty(self, mock_session):
        """Test Step Functions state machine discovery with empty response."""
        from aws_utils.services.stepfunctions import discover_state_machines

        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"stateMachines": []}]
        mock_client.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_client
        mock_session.return_value.region_name = "us-east-1"

        result = discover_state_machines()
        assert result == []


@pytest.mark.skip(reason="plan_distributor hook tests run separately")
class TestPlanDistributorParser:
    """Test plan distributor parser functions.

    These tests require the hooks directory to be in the path.
    Run separately with: uv run --directory /workspace/.claude/hooks/plan_distributor pytest
    """

    def test_extract_file_paths_from_table(self):
        """Test extracting paths from markdown table."""
        pass

    def test_extract_file_paths_from_backticks(self):
        """Test extracting paths from backtick-quoted text."""
        pass

    def test_detect_project_roots_claude_submodule(self):
        """Test detecting .claude submodule as project root."""
        pass

    def test_detect_project_roots_workspace(self):
        """Test detecting workspace root for non-.claude files."""
        pass
