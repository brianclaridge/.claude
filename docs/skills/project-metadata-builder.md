# project-metadata-builder Skill

> Build and update project metadata registry.

## Overview

Updates the project registry with discovered project information after analysis.

## Activation Triggers

- After project-analysis completes
- "update project metadata"
- "refresh projects"
- "register project"

## Data Stored

- Project name and path
- Technology stack
- Last activity timestamp
- Session history

## Configuration

In `config.yml`:
```yaml
project_metadata:
  session_history_limit: 10
  auto_update_on_session: true
  periodic_refresh_hours: 24
  stale_project_days: 30
```

## Output

Updates `${CLAUDE_PROJECTS_YML_PATH}` with project metadata.

## Source

[skills/project-metadata-builder/README.md](../../skills/project-metadata-builder/README.md)
