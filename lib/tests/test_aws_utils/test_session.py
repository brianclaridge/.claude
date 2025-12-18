"""Tests for aws_utils.core.session module."""

import pytest

from aws_utils.core.session import get_default_region


class TestGetDefaultRegion:
    """Tests for get_default_region function."""

    def test_returns_default_region(self, monkeypatch):
        """Should return AWS_DEFAULT_REGION if set."""
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
        result = get_default_region()
        assert result == "eu-west-1"

    def test_returns_fallback_when_not_set(self, monkeypatch):
        """Should return us-east-1 as fallback."""
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        result = get_default_region()
        assert result == "us-east-1"
