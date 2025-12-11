#!/usr/bin/env python3
"""
Video recording utility for Playwright automation.
Usage: python video_recorder.py <url> [--duration 10] [--output filename.webm]

Output: /workspace/.data/playwright/videos/
"""
import argparse
import os
import time
from datetime import datetime
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

VIDEO_DIR = "/workspace/.data/playwright/videos"


def record_video(
    url: str,
    duration: int = 10,
    output: str | None = None,
    width: int = 1280,
    height: int = 720,
) -> str:
    """Record a video of a URL and return the file path."""
    os.makedirs(VIDEO_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)

            print(f"Recording for {duration} seconds...")
            time.sleep(duration)

        finally:
            page.close()
            video_path = page.video.path() if page.video else None

            if video_path and output:
                new_path = os.path.join(VIDEO_DIR, output)
                os.rename(video_path, new_path)
                video_path = new_path

            if video_path:
                print(f"Video saved: {video_path}")

            context.close()
            browser.close()
            return video_path or ""


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

    args = parser.parse_args()
    record_video(args.url, args.duration, args.output, args.width, args.height)


if __name__ == "__main__":
    main()
