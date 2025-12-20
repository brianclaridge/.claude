"""Tests for screenshot utility."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.playwright_automation.screenshot import (
    SCREENCAP_DIR,
    take_screenshot,
)


class TestTakeScreenshot:
    """Tests for take_screenshot function."""

    def test_generates_filename_from_url(self, tmp_path, monkeypatch):
        """Test generates filename from URL domain and timestamp."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        # Mock playwright
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            result = take_screenshot("https://example.com/page")

            # Should include domain in filename
            assert "example-com" in result
            # Should end with .png
            assert result.endswith(".png")

    def test_uses_custom_output_filename(self, tmp_path, monkeypatch):
        """Test uses custom output filename."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            result = take_screenshot("https://example.com", output="custom.png")

            assert result.endswith("custom.png")

    def test_creates_output_directory(self, tmp_path, monkeypatch):
        """Test creates screencap directory if not exists."""
        screencap_dir = str(tmp_path / "screencaps")

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.SCREENCAP_DIR", screencap_dir):
            with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
                mock_sp.return_value.__enter__.return_value = mock_playwright

                take_screenshot("https://example.com")

                # Directory should be created
                assert (tmp_path / "screencaps").exists()

    def test_calls_page_goto_with_wait_strategy(self, tmp_path, monkeypatch):
        """Test calls page.goto with specified wait strategy."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            take_screenshot("https://example.com", wait_until="networkidle", timeout=60000)

            mock_page.goto.assert_called_once_with(
                "https://example.com",
                wait_until="networkidle",
                timeout=60000,
            )

    def test_calls_page_screenshot(self, tmp_path, monkeypatch):
        """Test calls page.screenshot with correct parameters."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            take_screenshot("https://example.com", full_page=True)

            mock_page.screenshot.assert_called_once()
            call_kwargs = mock_page.screenshot.call_args[1]
            assert call_kwargs["full_page"] is True

    def test_fallback_on_timeout(self, tmp_path, monkeypatch):
        """Test falls back to domcontentloaded on timeout."""
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        # First call raises timeout, second succeeds
        mock_page.goto.side_effect = [
            PlaywrightTimeoutError("timeout"),
            None,
        ]

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            # Should not raise, falls back
            take_screenshot("https://example.com", wait_until="networkidle")

            # Should be called twice - first with networkidle, then domcontentloaded
            assert mock_page.goto.call_count == 2

    def test_closes_browser(self, tmp_path, monkeypatch):
        """Test closes browser and context after screenshot."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            take_screenshot("https://example.com")

            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()

    def test_sets_viewport_size(self, tmp_path, monkeypatch):
        """Test sets viewport to 1920x1080."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.screenshot.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright

            take_screenshot("https://example.com")

            mock_browser.new_context.assert_called_once()
            call_kwargs = mock_browser.new_context.call_args[1]
            assert call_kwargs["viewport"] == {"width": 1920, "height": 1080}
