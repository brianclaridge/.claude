---
name: stack-manager
description: Recommend and bootstrap application stacks. Use when user says "suggest a stack", "bootstrap project", "what stack should I use", or invokes /stack-manager.
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
---

# Stack Manager

Recommend application stacks and bootstrap projects with predictable tooling.

## Activation Triggers

- User says "suggest a stack", "what stack should I use"
- User says "bootstrap project", "scaffold app"
- User invokes `/stack-manager` command
- Agent invokes this skill

## Stack Definitions

Stack definitions are stored in `.claude/stacks/*.md`. Each stack file follows a consistent schema with frontmatter metadata.

## Workflow

### Step 1: Selection Method

Present selection method options via AskUserQuestion:

```json
{
  "question": "How would you like to select a stack?",
  "header": "Method",
  "options": [
    {"label": "Interactive wizard", "description": "Answer questions about use case, language, complexity"},
    {"label": "Tag-based search", "description": "Provide tags to filter matching stacks"},
    {"label": "Show all stacks", "description": "View all available stacks with recommendations"},
    {"label": "AI analysis", "description": "Analyze project context for best match"}
  ],
  "multiSelect": false
}
```

### Step 2: Stack Selection

Execute the chosen selection method:

#### Interactive Wizard
1. Ask primary language preference (Python, TypeScript, Go)
2. Ask use case (web app, API, dashboard, CLI)
3. Ask complexity preference (beginner, intermediate, advanced)
4. Filter stacks matching criteria
5. Present matching stacks for selection

#### Tag-Based Search
1. Ask user for tags (comma-separated or space-separated)
2. Read all stack files from `.claude/stacks/`
3. Match tags against stack frontmatter
4. Present matching stacks ranked by match count

#### Show All Stacks
1. Read all stack files from `.claude/stacks/`
2. Display table with: Stack Name, Language, Use Cases, Complexity
3. Highlight recommended stack based on common patterns
4. Ask user to select from list

#### AI Analysis
1. Read project files (pyproject.toml, package.json, Dockerfile, etc.)
2. Analyze existing dependencies and patterns
3. Match against stack definitions
4. Recommend best-fit stack with explanation
5. Ask user to confirm or choose alternative

### Step 3: Bootstrap Method

After stack selection, present bootstrap method options:

```json
{
  "question": "How should I bootstrap the project?",
  "header": "Bootstrap",
  "options": [
    {"label": "Generate directly", "description": "Create files immediately in target directory"},
    {"label": "Cookiecutter template", "description": "Use cookiecutter for templated scaffolding"},
    {"label": "Step-by-step guided", "description": "Create each file with your confirmation"},
    {"label": "Dry-run first", "description": "Show what will be created, then execute"}
  ],
  "multiSelect": false
}
```

### Step 4: Execute Bootstrap

Execute the chosen bootstrap method:

#### Generate Directly
1. Read stack's Bootstrap section for file list
2. Create each file in target directory
3. Run initialization commands (uv init, npm create, etc.)
4. Report created files

#### Cookiecutter Template
1. Check if cookiecutter is available
2. Use stack's cookiecutter template URL if defined
3. Run cookiecutter with user inputs
4. Report created files

#### Step-by-Step Guided
1. For each file in Bootstrap section:
   - Show file content preview
   - Ask user to confirm creation
   - Create file if confirmed
2. Report created files

#### Dry-Run First
1. Display complete list of files to be created
2. Show directory structure that will result
3. Ask user to confirm
4. If confirmed, execute Generate Directly method
5. If declined, exit or ask for modifications

### Step 5: Post-Bootstrap

After bootstrap completion:

1. Display summary of created files
2. Show next steps from stack documentation:
   - Install dependencies command
   - Start development server command
   - Run tests command
3. Ask if user wants to run any commands

## Stack File Schema

Each stack file in `.claude/stacks/` follows this structure:

```yaml
---
id: stack-id-kebab-case
name: Human Readable Stack Name
tags: [language, framework, pattern]
complexity: beginner|intermediate|advanced
use_cases: [web-apps, apis, dashboards, cli]
---

## Frontend
- **Technology** - Brief description

## Backend
- **Technology** - Brief description

## DevOps
- **Technology** - Brief description

## Stack Maturity
| Component | Status | Notes |
|-----------|--------|-------|

## Rationale
Why choose this stack...

## Modern Alternatives
Alternative approaches to consider...

## Bootstrap

### Files Generated
- List of files created

### Commands
```bash
# Initialization commands
```

### Directory Structure
```text
project/
├── src/
└── ...
```
```

## Error Handling

| Error | Resolution |
|-------|------------|
| No stacks match criteria | Suggest broadening search, show all stacks |
| Target directory not empty | Warn user, ask to proceed or choose new directory |
| Missing dependencies | Report missing tools, provide install instructions |
| File creation failed | Report error, continue with remaining files |

## Safety Rules

**NEVER**:
- Overwrite existing files without user confirmation
- Delete files during bootstrap
- Run commands without displaying them first

**ALWAYS**:
- Confirm target directory before creating files
- Display file contents before creation in guided mode
- Report all created files after bootstrap
