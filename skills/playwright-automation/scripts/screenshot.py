#!/usr/bin/env python3
"""
Screenshot utility for Playwright automation.
Usage: python screenshot.py <url> [--full-page] [--wait-until STRATEGY] [--timeout MS] [--output filename.png]

Output: /workspace/.claude/.data/playwright/screencaps/
"""
import argparse
import os
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

SCREENCAP_DIR = "/workspace/.claude/.data/playwright/screencaps"

# Configure loguru
logger.add(
    "/workspace/.claude/.data/logs/playwright/screenshot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
)


def take_screenshot(
    url: str,
    full_page: bool = True,
    output: str | None = None,
    wait_until: str = "domcontentloaded",
    timeout: int = 30000,
) -> str:
    """Take a screenshot of a URL and return the file path.

    Args:
        url: URL to screenshot
        full_page: Capture full page or just viewport
        output: Output filename (auto-generated if None)
        wait_until: Wait strategy - domcontentloaded (default), load, or networkidle
        timeout: Navigation timeout in milliseconds (default 30000)

    Returns:
        Path to saved screenshot
    """
    os.makedirs(SCREENCAP_DIR, exist_ok=True)
    os.makedirs("/workspace/.claude/.data/logs/playwright", exist_ok=True)

    if output is None:
        domain = urlparse(url).netloc.replace(".", "-").replace(":", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"{domain}_{timestamp}.png"

    output_path = os.path.join(SCREENCAP_DIR, output)
    logger.info(f"Taking screenshot of {url} with wait_until={wait_until}, timeout={timeout}ms")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
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

        # Additional wait for dynamic content
        page.wait_for_timeout(2000)

        # Take screenshot
        page.screenshot(path=output_path, full_page=full_page)
        logger.info(f"Screenshot saved: {output_path}")
        print(f"Screenshot saved: {output_path}")

        context.close()
        browser.close()
        return output_path


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
    take_screenshot(args.url, args.full_page, args.output, args.wait_until, args.timeout)


if __name__ == "__main__":
    main()
