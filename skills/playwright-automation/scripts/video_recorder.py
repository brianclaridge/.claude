#!/usr/bin/env python3
"""
Video recording utility for Playwright automation.
Usage: python video_recorder.py <url> [--duration 10] [--wait-until STRATEGY] [--timeout MS] [--output filename]

Output: /workspace/.claude/.data/playwright/videos/
        Produces both .webm (native) and .mp4 (converted) formats.
"""
import argparse
import os
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

VIDEO_DIR = "/workspace/.claude/.data/playwright/videos"

# Configure loguru
logger.add(
    "/workspace/.claude/.data/logs/playwright/video_recorder.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
)


def convert_to_mp4(webm_path: str) -> str:
    """Convert WebM to MP4 using ffmpeg.

    Args:
        webm_path: Path to the WebM file

    Returns:
        Path to the converted MP4 file
    """
    mp4_path = webm_path.replace(".webm", ".mp4")
    logger.info(f"Converting to MP4: {mp4_path}")
    print(f"Converting to MP4...")
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            webm_path,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-y",
            "-loglevel",
            "error",
            mp4_path,
        ],
        check=True,
        capture_output=True,
    )
    logger.info(f"MP4 conversion complete: {mp4_path}")
    return mp4_path


def record_video(
    url: str,
    duration: int = 10,
    output: str | None = None,
    width: int = 1280,
    height: int = 720,
    wait_until: str = "domcontentloaded",
    timeout: int = 30000,
) -> tuple[str, str]:
    """Record a video of a URL and return paths to both WebM and MP4 files.

    Args:
        url: URL to record
        duration: Recording duration in seconds
        output: Output base filename without extension (auto-generated if None)
        width: Video width
        height: Video height
        wait_until: Wait strategy - domcontentloaded (default), load, or networkidle
        timeout: Navigation timeout in milliseconds (default 30000)

    Returns:
        Tuple of (webm_path, mp4_path)
    """
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs("/workspace/.claude/.data/logs/playwright", exist_ok=True)

    logger.info(f"Recording video of {url} for {duration}s with wait_until={wait_until}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()

        try:
            # Attempt navigation with specified strategy
            page.goto(url, wait_until=wait_until, timeout=timeout)
            logger.info(f"Navigation successful with {wait_until}")

        except PlaywrightTimeoutError:
            # Fallback to domcontentloaded if original strategy times out
            if wait_until != "domcontentloaded":
                logger.warning(
                    f"Timeout with {wait_until}, falling back to domcontentloaded"
                )
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                    logger.info("Fallback navigation successful")
                except PlaywrightTimeoutError:
                    logger.error(f"Navigation failed even with fallback: {url}")
                    raise
            else:
                logger.error(f"Navigation timeout: {url}")
                raise

        # Record for specified duration
        print(f"Recording for {duration} seconds...")
        logger.info(f"Recording for {duration} seconds")
        time.sleep(duration)

        # CRITICAL: Get video path BEFORE closing page
        video = page.video
        video_path = video.path() if video else None

        # Now safe to close
        page.close()

        # Close context first - video is only fully written after context.close()
        context.close()
        browser.close()

        # Rename if custom output specified
        if video_path and output:
            # Ensure .webm extension for the base file
            base_name = output.replace(".webm", "").replace(".mp4", "")
            new_path = os.path.join(VIDEO_DIR, f"{base_name}.webm")
            os.rename(video_path, new_path)
            video_path = new_path

        webm_path = video_path or ""
        mp4_path = ""

        if webm_path:
            logger.info(f"WebM saved: {webm_path}")
            print(f"Video saved (WebM): {webm_path}")

            # Convert to MP4
            mp4_path = convert_to_mp4(webm_path)
            print(f"Video saved (MP4):  {mp4_path}")

        return (webm_path, mp4_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record website video")
    parser.add_argument("url", help="URL to record")
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=10,
        help="Recording duration in seconds (default: 10)",
    )
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--width", type=int, default=1280, help="Video width")
    parser.add_argument("--height", type=int, default=720, help="Video height")
    parser.add_argument(
        "--wait-until",
        "-w",
        choices=["domcontentloaded", "load", "networkidle"],
        default="domcontentloaded",
        help="Wait strategy (default: domcontentloaded)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=30000,
        help="Navigation timeout in ms (default: 30000)",
    )

    args = parser.parse_args()
    record_video(
        args.url,
        args.duration,
        args.output,
        args.width,
        args.height,
        args.wait_until,
        args.timeout,
    )


if __name__ == "__main__":
    main()
