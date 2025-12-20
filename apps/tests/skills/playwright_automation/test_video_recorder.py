"""Tests for video recorder utility."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from claude_apps.skills.playwright_automation.video_recorder import (
    VIDEO_DIR,
    convert_to_mp4,
    record_video,
)


class TestConvertToMp4:
    """Tests for convert_to_mp4 function."""

    def test_converts_webm_to_mp4(self, tmp_path):
        """Test converts WebM file to MP4."""
        webm_path = str(tmp_path / "test.webm")
        mp4_path = str(tmp_path / "test.mp4")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = convert_to_mp4(webm_path)

            assert result == mp4_path
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert webm_path in call_args
            assert mp4_path in call_args

    def test_returns_empty_on_ffmpeg_error(self, tmp_path):
        """Test returns empty string on FFmpeg error."""
        webm_path = str(tmp_path / "test.webm")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "ffmpeg", stderr=b"Error"
            )

            result = convert_to_mp4(webm_path)

            assert result == ""

    def test_returns_empty_when_ffmpeg_not_found(self, tmp_path):
        """Test returns empty string when FFmpeg not installed."""
        webm_path = str(tmp_path / "test.webm")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffmpeg not found")

            result = convert_to_mp4(webm_path)

            assert result == ""


class TestRecordVideo:
    """Tests for record_video function."""

    def test_creates_output_directory(self, tmp_path, monkeypatch):
        """Test creates video directory if not exists."""
        video_dir = str(tmp_path / "videos")

        mock_video = MagicMock()
        mock_video.path.return_value = str(tmp_path / "video.webm")

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.VIDEO_DIR", video_dir):
            with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
                mock_sp.return_value.__enter__.return_value = mock_playwright
                with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                    mock_convert.return_value = ""
                    with patch("time.sleep"):  # Don't actually sleep
                        record_video("https://example.com", duration=1)

                        assert (tmp_path / "videos").exists()

    def test_configures_video_recording(self, tmp_path, monkeypatch):
        """Test configures browser context for video recording."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_video = MagicMock()
        mock_video.path.return_value = str(tmp_path / "video.webm")

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                mock_convert.return_value = ""
                with patch("time.sleep"):
                    record_video("https://example.com", width=1280, height=720)

                    mock_browser.new_context.assert_called_once()
                    call_kwargs = mock_browser.new_context.call_args[1]
                    assert "record_video_dir" in call_kwargs
                    assert call_kwargs["record_video_size"] == {"width": 1280, "height": 720}

    def test_calls_page_goto(self, tmp_path, monkeypatch):
        """Test calls page.goto with URL."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_video = MagicMock()
        mock_video.path.return_value = str(tmp_path / "video.webm")

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                mock_convert.return_value = ""
                with patch("time.sleep"):
                    record_video("https://example.com", wait_until="load", timeout=60000)

                    mock_page.goto.assert_called_once_with(
                        "https://example.com",
                        wait_until="load",
                        timeout=60000,
                    )

    def test_sleeps_for_duration(self, tmp_path, monkeypatch):
        """Test sleeps for specified duration."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_video = MagicMock()
        mock_video.path.return_value = str(tmp_path / "video.webm")

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                mock_convert.return_value = ""
                with patch("time.sleep") as mock_sleep:
                    record_video("https://example.com", duration=15)

                    mock_sleep.assert_called_once_with(15)

    def test_returns_webm_and_mp4_paths(self, tmp_path, monkeypatch):
        """Test returns tuple of WebM and MP4 paths."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        webm_path = str(tmp_path / "video.webm")
        mp4_path = str(tmp_path / "video.mp4")

        mock_video = MagicMock()
        mock_video.path.return_value = webm_path

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                mock_convert.return_value = mp4_path
                with patch("time.sleep"):
                    result = record_video("https://example.com")

                    assert result == (webm_path, mp4_path)

    def test_closes_page_context_browser(self, tmp_path, monkeypatch):
        """Test closes page, context, and browser after recording."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_video = MagicMock()
        mock_video.path.return_value = str(tmp_path / "video.webm")

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                mock_convert.return_value = ""
                with patch("time.sleep"):
                    record_video("https://example.com")

                    mock_page.close.assert_called_once()
                    mock_context.close.assert_called_once()
                    mock_browser.close.assert_called_once()

    def test_renames_video_with_custom_output(self, tmp_path, monkeypatch):
        """Test renames video file when output specified."""
        # Set up video directory in tmp_path
        video_dir = tmp_path / "videos"
        video_dir.mkdir(parents=True)
        original_path = video_dir / "random-id.webm"
        original_path.write_text("video data")

        mock_video = MagicMock()
        mock_video.path.return_value = str(original_path)

        mock_page = MagicMock()
        mock_page.video = mock_video

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.VIDEO_DIR", str(video_dir)):
            with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
                mock_sp.return_value.__enter__.return_value = mock_playwright
                with patch("claude_apps.skills.playwright_automation.video_recorder.convert_to_mp4") as mock_convert:
                    mock_convert.return_value = ""
                    with patch("time.sleep"):
                        webm_path, _ = record_video("https://example.com", output="my-video")

                        assert webm_path.endswith("my-video.webm")

    def test_handles_no_video(self, tmp_path, monkeypatch):
        """Test handles case when no video is recorded."""
        monkeypatch.setenv("CLAUDE_PATH", str(tmp_path))

        mock_page = MagicMock()
        mock_page.video = None

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("claude_apps.skills.playwright_automation.video_recorder.sync_playwright") as mock_sp:
            mock_sp.return_value.__enter__.return_value = mock_playwright
            with patch("time.sleep"):
                result = record_video("https://example.com")

                assert result == ("", "")
