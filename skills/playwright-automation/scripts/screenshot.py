#!/usr/bin/env python3
"""
Screenshot utility for Playwright automation.
Usage: python screenshot.py <url> [--full-page] [--output filename.png]

Output: /workspace/.data/playwright/screencaps/
"""
import argparse
import os
from datetime import datetime
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

SCREENCAP_DIR = "/workspace/.data/playwright/screencaps"


def take_screenshot(url: str, full_page: bool = True, output: str | None = None) -> str:
    """Take a screenshot of a URL and return the file path."""
    os.makedirs(SCREENCAP_DIR, exist_ok=True)

    if output is None:
        domain = urlparse(url).netloc.replace(".", "-").replace(":", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"{domain}_{timestamp}.png"

    output_path = os.path.join(SCREENCAP_DIR, output)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.screenshot(path=output_path, full_page=full_page)
            print(f"Screenshot saved: {output_path}")
            return output_path
        finally:
            context.close()
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Take website screenshots")
    parser.add_argument("url", help="URL to screenshot")
    parser.add_argument(
        "--full-page",
        action="store_true",
        default=True,
        help="Capture full page (default: True)",
    )
    parser.add_argument("--output", "-o", help="Output filename")

    args = parser.parse_args()
    take_screenshot(args.url, args.full_page, args.output)


if __name__ == "__main__":
    main()
