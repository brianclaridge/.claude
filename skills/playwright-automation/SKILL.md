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
/workspace/.data/playwright/
├── screencaps/    # Screenshots (.png, .jpg)
├── videos/        # Recordings (.webm)
├── pdfs/          # Generated PDFs
├── traces/        # Debug traces (.zip)
└── data/          # Extracted data (.json, .csv)
```

## Utility Scripts

### Screenshot Utility
```bash
uv run python /workspace/.claude/skills/playwright-automation/scripts/screenshot.py <url> [--full-page] [--output filename.png]
```

### Video Recorder
```bash
uv run python /workspace/.claude/skills/playwright-automation/scripts/video_recorder.py <url> [--duration 10] [--output filename.webm]
```

## Script Template

Use this template for custom automation scripts:

```python
#!/usr/bin/env python3
"""
Browser automation script: [DESCRIPTION]
Output: /workspace/.data/playwright/[TYPE]/[FILENAME]
"""
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

SCREENCAP_DIR = "/workspace/.data/playwright/screencaps"
VIDEO_DIR = "/workspace/.data/playwright/videos"
DATA_DIR = "/workspace/.data/playwright/data"

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
            # Your automation code here
            page.goto("https://example.com")
            page.screenshot(path=f"{SCREENCAP_DIR}/example_{timestamp}.png", full_page=True)
        finally:
            page.close()
            if page.video:
                print(f"Video saved: {page.video.path()}")
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
```

## Common Patterns

### Screenshot Capture
```python
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
# Enable in context creation
context = browser.new_context(
    record_video_dir=VIDEO_DIR,
    record_video_size={"width": 1280, "height": 720}
)
page = context.new_page()
# ... perform actions ...
page.close()  # Video saved when page closes
video_path = page.video.path()
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

title = page.locator("h1").text_content()
items = page.locator(".item").all()
data = [item.text_content() for item in items]

with open(f"{DATA_DIR}/extracted.json", "w") as f:
    json.dump({"title": title, "items": data}, f, indent=2)
```

### Wait Strategies
```python
page.wait_for_selector("#dynamic-content")
page.wait_for_url("**/success")
page.wait_for_load_state("networkidle")
page.wait_for_selector("#slow-element", timeout=60000)
```

### Error Handling
```python
from playwright.sync_api import TimeoutError

try:
    page.click("#button", timeout=5000)
except TimeoutError:
    print("Button not found, trying alternative...")
    page.click(".fallback-button")
```

### Tracing for Debug
```python
context.tracing.start(screenshots=True, snapshots=True, sources=True)
# ... perform actions ...
context.tracing.stop(path=f"{DATA_DIR}/trace.zip")
# View with: playwright show-trace trace.zip
```

## Execution

Run scripts with uv:
```bash
uv run python /path/to/script.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser launch fails | Ensure `headless=True` in container |
| Element not found | Use `wait_for_selector()` before interaction |
| Video not saved | Ensure `page.close()` is called |
| Permission denied | Check output directory permissions |
| Timeout errors | Increase timeout or check network |
