#!/usr/bin/env python3
"""
Twitch navigation test: Find top streamer and their game.
Output:
  - Screenshot: /workspace/.claude/.data/playwright/screencaps/twitch-top-streamer.png
  - Data: /workspace/.claude/.data/playwright/data/twitch-top-streamer.json
"""
import json
import os
from datetime import datetime

import structlog
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# Use CLAUDE_PATH environment variable with fallback
CLAUDE_PATH = os.environ.get("CLAUDE_PATH", "/workspace/.claude")
SCREENCAP_DIR = os.path.join(CLAUDE_PATH, ".data/playwright/screencaps")
DATA_DIR = os.path.join(CLAUDE_PATH, ".data/playwright/data")
LOG_DIR = os.path.join(CLAUDE_PATH, ".data/logs/playwright")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO+
)
logger = structlog.get_logger()


def main() -> None:
    os.makedirs(SCREENCAP_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs("/workspace/.claude/.data/logs/playwright", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("Starting Twitch navigation test")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # 1. Navigate to Twitch
            logger.info("Navigating to Twitch homepage")
            page.goto("https://twitch.tv", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Take initial screenshot of homepage
            homepage_path = f"{SCREENCAP_DIR}/twitch-homepage_{timestamp}.png"
            page.screenshot(path=homepage_path, full_page=False)
            logger.info(f"Homepage screenshot saved: {homepage_path}")

            # 2. Find top streamer - try multiple selectors
            logger.info("Looking for top streamer")
            streamer_name = None
            streamer_link = None

            # Try different selectors for streamer cards
            selectors = [
                '[data-a-target="preview-card-channel-link"]',
                'a[data-a-target="preview-card-title-link"]',
                '.tw-link[href*="/videos/"]',
                'a[href^="/"][class*="ScCoreLink"]',
            ]

            for selector in selectors:
                try:
                    locator = page.locator(selector).first
                    if locator.count() > 0:
                        streamer_link = locator
                        # Try to get text or nearby text
                        text = locator.text_content(timeout=3000)
                        if text and text.strip():
                            streamer_name = text.strip()
                            logger.info(f"Found streamer with selector {selector}: {streamer_name}")
                            break
                except Exception:
                    continue

            # If no name found, try to extract from any visible stream card
            if not streamer_name:
                try:
                    # Look for any channel name element
                    channel_elem = page.locator('[data-a-target="preview-card-channel-link"] p').first
                    streamer_name = channel_elem.text_content(timeout=3000)
                    streamer_link = page.locator('[data-a-target="preview-card-channel-link"]').first
                    logger.info(f"Found streamer from channel element: {streamer_name}")
                except Exception:
                    pass

            if not streamer_name:
                streamer_name = "Unknown"
                logger.warning("Could not determine streamer name")

            # 3. Click into the stream if we found a link
            if streamer_link:
                try:
                    logger.info("Clicking into stream")
                    streamer_link.click(timeout=5000)
                    page.wait_for_timeout(4000)
                except Exception as e:
                    logger.warning(f"Could not click stream link: {e}")

            # 4. Extract stream info from channel page
            game = "Unknown"
            viewers = "Unknown"

            # Try to get game/category
            game_selectors = [
                '[data-a-target="stream-game-link"]',
                'a[href*="/directory/category/"]',
                '[data-a-target="player-info-game-name"]',
            ]

            for selector in game_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.count() > 0:
                        text = elem.text_content(timeout=3000)
                        if text and text.strip():
                            game = text.strip()
                            logger.info(f"Found game: {game}")
                            break
                except Exception:
                    continue

            # Try to get viewer count
            viewer_selectors = [
                '[data-a-target="animated-channel-viewers-count"]',
                '[aria-label*="viewer"]',
                '.tw-animated-number',
            ]

            for selector in viewer_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.count() > 0:
                        text = elem.text_content(timeout=3000)
                        if text and text.strip():
                            viewers = text.strip()
                            logger.info(f"Found viewers: {viewers}")
                            break
                except Exception:
                    continue

            # 5. Take screenshot of stream page
            stream_path = f"{SCREENCAP_DIR}/twitch-top-streamer_{timestamp}.png"
            page.screenshot(path=stream_path, full_page=False)
            logger.info(f"Stream screenshot saved: {stream_path}")

            # 6. Save data
            data = {
                "timestamp": timestamp,
                "streamer": streamer_name,
                "game": game,
                "viewers": viewers,
                "screenshots": {
                    "homepage": homepage_path,
                    "stream": stream_path,
                },
            }

            data_path = f"{DATA_DIR}/twitch-top-streamer_{timestamp}.json"
            with open(data_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Data saved: {data_path}")

            # Print results
            print(f"\n{'='*50}")
            print("Twitch Navigation Test Results")
            print(f"{'='*50}")
            print(f"Top Streamer: {streamer_name}")
            print(f"Playing: {game}")
            print(f"Viewers: {viewers}")
            print(f"\nScreenshots:")
            print(f"  Homepage: {homepage_path}")
            print(f"  Stream: {stream_path}")
            print(f"\nData: {data_path}")
            print(f"{'='*50}\n")

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error: {e}")
            # Take error screenshot
            error_path = f"{SCREENCAP_DIR}/twitch-error_{timestamp}.png"
            page.screenshot(path=error_path)
            logger.info(f"Error screenshot saved: {error_path}")
            raise

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
