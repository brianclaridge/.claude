# Plan: Plan Distribution Fix + Python Project Consolidation

**Affects:** `/workspace/.claude/` (hooks, rules, lib, skills)

---

## Part 1: Fix Plan Distribution System

### Problem Statement
1. `plan_distributor` hook didn't fire on ExitPlanMode (silent failure)
2. Plans distributed to multiple locations instead of single `${CLAUDE_PLANS_PATH}`
3. Filename uses random names instead of `YYYYMMDD_HHMMSS_topic.md`

### Changes Required

#### 1.1 Update Rule 040 (plans)
- Remove submodule exception - ALL plans go to `${CLAUDE_PLANS_PATH}`
- Add requirement: Plan header must include absolute paths affected
- Clarify: Claude Code's random plan names are internal; Rule 040 naming applies to canonical copy

#### 1.2 Fix plan_distributor Hook
- **File**: `/workspace/.claude/hooks/plan_distributor/src/distributor.py`
- Change: Distribute ONLY to `${CLAUDE_PLANS_PATH}` (remove dual-location logic)
- Add: Rename file to `YYYYMMDD_HHMMSS_<topic>.md` format

#### 1.3 Fix plan_distributor Hook (parser.py)
- **File**: `/workspace/.claude/hooks/plan_distributor/src/parser.py`
- Change: `detect_project_roots()` returns single destination: `${CLAUDE_PLANS_PATH}`
- Add: Extract topic from plan content for filename

#### 1.4 Debug Hook Execution
- Verify venv is properly initialized
- Add error logging to hook entry point
- Test hook fires correctly on ExitPlanMode

---

## Part 2: Python Project Consolidation

## Summary
Consolidate 17 separate Python projects under `.claude/` into a single `claude_apps` package with submodules for `hooks`, `skills`, and `shared`.

## Target Architecture

```
.claude/
├── pyproject.toml              # Single consolidated pyproject.toml
├── uv.lock                     # Single lock file
├── apps/
│   └── src/claude_apps/
│       ├── __init__.py
│       ├── hooks/              # 8 hooks migrated
│       │   ├── logger/
│       │   ├── rules_loader/
│       │   ├── session_context_injector/
│       │   ├── cloud_auth_prompt/
│       │   ├── submodule_auto_updater/
│       │   ├── plan_distributor/
│       │   ├── playwright_healer/
│       │   └── changelog_monitor/
│       ├── skills/             # Skills with Python code
│       │   ├── git_manager/
│       │   ├── aws_login/
│       │   ├── gcp_login/
│       │   └── ...
│       └── shared/             # Current lib/ content
│           ├── aws_utils/
│           ├── config_helper/
│           └── subprocess_helper/
├── skills/                     # KEEP - .md files only
└── lib/                        # ELIMINATE after migration
```

## Key Decisions
- **Package name**: `claude_apps`
- **Import style**: Absolute (`from claude_apps.shared import aws_utils`)
- **Root location**: `.claude/pyproject.toml`
- **Skill structure**: Separate .md (in skills/) from Python (in apps/skills/)

## Implementation Phases

### Phase 1: Infrastructure Setup
1. Create directory structure: `.claude/apps/src/claude_apps/{hooks,skills,shared}`
2. Create `__init__.py` files for package hierarchy
3. Create consolidated `.claude/pyproject.toml`

### Phase 2: Migrate Shared Library
4. Copy `.claude/lib/aws_utils/` → `.claude/apps/src/claude_apps/shared/aws_utils/`
5. Copy `.claude/lib/config_helper/` → `.claude/apps/src/claude_apps/shared/config_helper/`
6. Copy `.claude/lib/subprocess_helper/` → `.claude/apps/src/claude_apps/shared/subprocess_helper/`
7. Update imports to absolute style

### Phase 3: Migrate Hooks (8 total)
For each hook in [logger, rules_loader, session_context_injector, cloud_auth_prompt, submodule_auto_updater, plan_distributor, playwright_healer, changelog_monitor]:
- Copy `.claude/hooks/<name>/src/*.py` → `.claude/apps/src/claude_apps/hooks/<name>/`
- Create `__main__.py` as entry point
- Update imports to absolute style

### Phase 4: Migrate Skills
For skills with Python code:
- Copy scripts/src to `.claude/apps/src/claude_apps/skills/<name>/`
- Update imports to absolute style

### Phase 5: Update Hook Invocations
Update `.claude/config/templates/settings.json`:

| Old | New |
|-----|-----|
| `uv run --directory {{ .Env.CLAUDE_HOOKS_PATH }}/logger python -m src` | `uv run --directory {{ .Env.CLAUDE_PATH }} python -m claude_apps.hooks.logger` |
| (same pattern for all 8 hooks) | |

### Phase 6: Cleanup
- Run `uv lock` from `.claude/`
- Run tests: `uv run pytest`
- Delete `.claude/lib/`, old `.claude/hooks/*/{pyproject.toml,uv.lock,.venv,src/}`
- Delete old skill Python directories

## Critical Files to Modify
- `.claude/pyproject.toml` (CREATE)
- `.claude/config/templates/settings.json` (UPDATE hook commands)
- All Python files (UPDATE imports)

## Hook Command Changes
```json
// OLD
"uv run --directory {{ .Env.CLAUDE_HOOKS_PATH }}/logger python -m src"

// NEW
"uv run --directory {{ .Env.CLAUDE_PATH }} python -m claude_apps.hooks.logger"
```

## Validation
1. All tests pass: `uv run --directory .claude pytest`
2. Each hook invocable: `uv run --directory .claude python -m claude_apps.hooks.<name>`
3. Shared imports work: `from claude_apps.shared.config_helper import get_hook_config`
4. Start Claude session to verify hooks fire
