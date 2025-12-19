# browser-automation Agent

> Playwright browser automation for screenshots, video, and scraping.

## Overview

Executes browser automation tasks using Playwright. Handles navigation, screenshots, video recording, and data extraction.

## Invocation

```
/playwright
```

Or triggered by:
- "take screenshot of..."
- "record video of..."
- "scrape data from..."
- "browse to..."

## Capabilities

- Page navigation
- Screenshot capture
- Video recording
- Data extraction
- Form filling
- Multi-page workflows

## Skills Used

- `playwright-automation` - Browser scripts

## Output

Artifacts stored in `.data/playwright/`:
- Screenshots (PNG/JPEG)
- Videos (WebM)
- Traces
- Extracted data

## Configuration

Playwright MCP server configured in `settings.json`.

## Source

[agents/browser-automation.md](../../agents/browser-automation.md)
