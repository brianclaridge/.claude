# Claude Code Feature Roadmap

Last updated: 2025-12-13
Last checked: (not yet checked)

This document tracks Claude Code features and opportunities for the .claude environment.

## How This Works

The `changelog_monitor` hook automatically:
1. Fetches the Claude Code changelog on session start
2. Parses new versions since last check
3. Identifies hook and skill opportunities
4. Injects relevant updates into session context

## New Features to Evaluate

No features evaluated yet. The changelog monitor will populate this section.

## Hook Opportunities

Hook events that could be leveraged:
- (populated automatically by changelog monitor)

## Skill Opportunities

New capabilities that could become skills:
- (populated automatically by changelog monitor)

## Breaking Changes (Action Required)

Changes that may require updates:
- (populated automatically by changelog monitor)

## Implementation Backlog

Features we plan to implement:

### High Priority
- [ ] (add items here)

### Medium Priority
- [ ] (add items here)

### Low Priority
- [ ] (add items here)

## Version History

Recent Claude Code versions will be tracked here by the changelog monitor.

---

## Manual Updates

To manually refresh this document:

```bash
# Force refresh changelog cache
uv run --directory ${CLAUDE_PATH}/hooks/changelog_monitor python -c "
from src.fetcher import fetch_changelog
from src.parser import parse_changelog
from src.analyzer import analyze_versions, generate_roadmap_content

content = fetch_changelog(force_refresh=True)
versions = parse_changelog(content)
result = analyze_versions(versions)
print(generate_roadmap_content(result, None))
"
```
