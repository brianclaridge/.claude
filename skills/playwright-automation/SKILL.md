---
name: playwright-automation
description: Execute complex browser automation using Playwright Python. Use for video recording, multi-page navigation, data extraction. Triggers on "browser script", "record video of website", "extract data from webpage".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Playwright Automation Skill

Python-based browser automation for complex workflows requiring video recording, multi-page navigation, or data extraction.

## When to Use

- Video recording of browser interactions
- Multi-page navigation sequences
- Data extraction with post-processing
- Form filling with validation
- Screenshot sequences or comparisons
- Any automation requiring Python logic

## Output Directories

```
/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/
├── screencaps/    # Screenshots (.png, .jpg)
├── videos/        # Recordings (.webm)
├── pdfs/          # Generated PDFs
├── traces/        # Debug traces (.zip)
└── data/          # Extracted data (.json, .csv)
```

## Wait Strategy Guide

| Strategy | Use Case | Speed | Reliability |
|----------|----------|-------|-------------|
| `domcontentloaded` | General web pages (default) | Fast (1-3s) | High |
| `load` | Media-heavy sites, SPAs | Medium (2-5s) | High |
| `networkidle` | Static sites that fully settle | Slow (5-30s+) | Variable |

**Recommendation:** Use `domcontentloaded` (default) for most sites. Only use `networkidle` for static pages where you need all resources loaded.

## Utility Scripts

### Screenshot Utility
```bash
cd /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/playwright-automation && \
uv run python scripts/screenshot.py <url> \
  [--full-page] \
  [--wait-until domcontentloaded|load|networkidle] \
  [--timeout 30000] \
  [--output filename.png]
```

### Video Recorder
```bash
cd /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/playwright-automation && \
uv run python scripts/video_recorder.py <url> \
  [--duration 10] \
  [--wait-until domcontentloaded|load|networkidle] \
  [--timeout 30000] \
  [--output filename.webm]
```

## Script Template

Use this template for custom automation scripts:

```python
#!/usr/bin/env python3
"""
Browser automation script: [DESCRIPTION]
Output: /workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/[TYPE]/[FILENAME]
"""
import os
from datetime import datetime
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCREENCAP_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/screencaps"
VIDEO_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/videos"
DATA_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/data"

os.makedirs(SCREENCAP_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            # Navigate with fallback
            page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)  # Allow dynamic content to load

            # Your automation code here
            page.screenshot(path=f"{SCREENCAP_DIR}/example_{timestamp}.png", full_page=True)

        except PlaywrightTimeoutError:
            logger.error("Navigation timeout")
            raise
        finally:
            # Get video path BEFORE closing page
            video = page.video
            video_path = video.path() if video else None

            page.close()
            if video_path:
                print(f"Video saved: {video_path}")
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
```

## Common Patterns

### Screenshot Capture
```python
SCREENCAP_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/screencaps"

# Full page
page.screenshot(path=f"{SCREENCAP_DIR}/full.png", full_page=True)

# Viewport only
page.screenshot(path=f"{SCREENCAP_DIR}/viewport.png")

# Specific element
page.locator("#element").screenshot(path=f"{SCREENCAP_DIR}/element.png")

# With options
page.screenshot(
    path=f"{SCREENCAP_DIR}/custom.jpg",
    type="jpeg",
    quality=80,
    clip={"x": 0, "y": 0, "width": 800, "height": 600}
)
```

### Video Recording
```python
VIDEO_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/videos"

# Enable in context creation
context = browser.new_context(
    record_video_dir=VIDEO_DIR,
    record_video_size={"width": 1280, "height": 720}
)
page = context.new_page()
# ... perform actions ...

# CRITICAL: Get path BEFORE closing
video = page.video
video_path = video.path() if video else None
page.close()  # Video finalized here
```

### Form Interaction
```python
page.fill("#username", "testuser")
page.fill("#password", "testpass")
page.click("button[type='submit']")
page.select_option("#country", "US")
page.check("#agree-terms")
page.set_input_files("#file-upload", "/path/to/file.pdf")
```

### Data Extraction
```python
import json

DATA_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/data"

title = page.locator("h1").text_content()
items = page.locator(".item").all()
data = [item.text_content() for item in items]

with open(f"{DATA_DIR}/extracted.json", "w") as f:
    json.dump({"title": title, "items": data}, f, indent=2)
```

### Wait Strategies
```python
# Wait for specific element
page.wait_for_selector("#dynamic-content")

# Wait for URL change
page.wait_for_url("**/success")

# Wait for load state (use sparingly)
page.wait_for_load_state("networkidle")

# Custom timeout
page.wait_for_selector("#slow-element", timeout=60000)

# Fixed delay for dynamic content
page.wait_for_timeout(2000)
```

### Error Handling with Fallback
```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

try:
    page.goto(url, wait_until="networkidle", timeout=30000)
except PlaywrightTimeoutError:
    # Fallback to faster strategy
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
```

### Tracing for Debug
```python
DATA_DIR = "/workspace/${CLAUDE_PROJECT_SLUG}/.claude/.data/playwright/data"

context.tracing.start(screenshots=True, snapshots=True, sources=True)
# ... perform actions ...
context.tracing.stop(path=f"{DATA_DIR}/trace.zip")
# View with: playwright show-trace trace.zip
```

## Execution

Run scripts using uv from the skill directory:
```bash
cd /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/playwright-automation && uv run python scripts/<script>.py
```

Or for custom scripts in other locations:
```bash
cd /workspace/${CLAUDE_PROJECT_SLUG}/.claude/skills/playwright-automation && uv run python /path/to/custom_script.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser launch fails | Ensure `headless=True` in container |
| Element not found | Use `wait_for_selector()` before interaction |
| Video not saved | Get `page.video.path()` BEFORE `page.close()` |
| Permission denied | Check output directory permissions |
| Timeout errors | Use `domcontentloaded` instead of `networkidle` |
| Streaming sites timeout | Add `page.wait_for_timeout(3000)` after navigation |
