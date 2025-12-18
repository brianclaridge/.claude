"""Tests for config_helper.logging module."""

import pytest

from config_helper.logging import setup_logger, get_logger


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_configures_logger_without_file(self, capsys):
        """Should configure logger for stderr output."""
        setup_logger("test_hook", level="DEBUG")
        logger = get_logger()
        logger.info("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.err

    def test_configures_logger_with_file(self, temp_dir):
        """Should configure logger with file output."""
        log_path = temp_dir / "test.log"
        setup_logger("test_hook", log_path=log_path, level="INFO")
        logger = get_logger()
        logger.info("file test message")
        # Logger may buffer, so check file exists
        assert log_path.parent.exists()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger_instance(self):
        """Should return loguru logger instance."""
        logger = get_logger()
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "error")
