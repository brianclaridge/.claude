# Plan: Migrate Directives to Native Rules System

## Summary

Refactor the custom `directives/` system to use Claude Code's native `.claude/rules/` feature, while preserving optional per-message reinforcement via configurable toggle.

## Research Summary

### Claude Code Native Memory System

| Feature | Location | Behavior |
|---------|----------|----------|
| CLAUDE.md | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Project-level instructions, shared via source control |
| CLAUDE.local.md | `./CLAUDE.local.md` | Personal project instructions (auto-gitignored) |
| User memory | `~/.claude/CLAUDE.md` | Personal preferences across all projects |
| Rules directory | `.claude/rules/*.md` | Modular topic-specific rules |
| Conditional rules | `paths:` frontmatter | Apply rules only to specific file patterns |

**Native Loading Behavior:**
- Rules loaded automatically at session start
- Recursive discovery from CWD to repo root
- Path-conditional rules evaluated per file context
- No custom hooks required

### Current Directive System

| Component | Location | Purpose |
|-----------|----------|---------|
| Directives | `.claude/directives/*.md` | Rule files (000-080 numbered) |
| Hook | `.claude/hooks/directive_loader/` | Python hook to inject directives |
| Config | `hooks/directive_loader/config.json` | Path configuration |
| Triggers | SessionStart, UserPromptSubmit | When directives are injected |

**Current Loading Behavior:**
- Loads ALL directives on EVERY SessionStart AND UserPromptSubmit
- Alphabetical ordering via numeric prefixes (000, 010, 020...)
- Returns via `additionalContext` hook output
- Custom Python implementation (~200 lines)

## Critical Difference

| Aspect | Native Rules | directive_loader |
|--------|--------------|------------------|
| Load frequency | Session start only | Every user message |
| Reinforcement | Once per session | Continuous |
| Maintenance | Zero (built-in) | Custom Python code |
| Conditional | `paths:` frontmatter | None (all always load) |
| Ordering | Alphabetical | Numeric prefix |

**The key distinction:** Your directive_loader injects rules on EVERY `UserPromptSubmit`, which reinforces directives throughout the conversation. Native rules load once at session start.

## Selected Approach: Hybrid with Native Rules Priority

**User Decisions:**
1. Session-start loading by default (native rules)
2. Per-message reinforcement OFF by default, configurable via toggle
3. directive_loader becomes optional, reads from `./rules/` (not `./directives/`)

### Implementation

1. **Migrate files:** `directives/*.md` → `rules/*.md`
2. **Add config toggle:** `config.yml` → `directive_reinforcement: false` (default)
3. **Update hook path:** directive_loader reads from `./rules/`
4. **Conditional execution:** Hook checks toggle before injecting on UserPromptSubmit
5. **Native rules:** Claude Code automatically loads `./rules/*.md` at session start

## File Changes

### Directory Migration
```
.claude/directives/ → .claude/rules/
├── 000-directives.md
├── 010-start.md
├── 020-persona.md
├── 030-agents.md
├── 040-plans.md
├── 050-python.md
├── 060-context7.md
├── 070-backward-compat.md
└── 080-ask-user-questions.md
```

### Hook Rename

Rename hook directory for consistency:
```
.claude/hooks/directive_loader/ → .claude/hooks/rules_loader/
```

### Config Updates

**`.claude/config.yml`** - Add toggle with per-rule overrides:
```yaml
rules_loader:
  reinforcement_enabled: false  # Global default for per-message injection
  rules_path: rules/            # Source directory for rules
  rules:                        # Per-rule reinforcement overrides
    000-directives:
      reinforce: true           # Critical rule - always reinforce
    010-start:
      reinforce: false          # Session start only
    020-persona:
      reinforce: true           # Persona reminder
    # Rules not listed inherit global reinforcement_enabled value
```

**`.claude/hooks/rules_loader/config.json`** - Update path:
```json
{
  "rules_path": "${CLAUDE_PATH}/rules",
  "log_base_path": "${CLAUDE_PATH}/.data/logs/rules_loader"
}
```

### Hook Modifications

**`.claude/hooks/rules_loader/src/__main__.py`**:
- Read `config.yml` to check `reinforcement_enabled`
- If `false` and event is `UserPromptSubmit`: exit early with empty response
- If `true` or event is `SessionStart`: load and inject rules

**`.claude/settings.json`**:
- Update hook paths from `directive_loader` to `rules_loader`
- Keep both SessionStart and UserPromptSubmit hooks (hook self-disables based on config)

### Critical Files Modified

| File | Change |
|------|--------|
| `.claude/hooks/directive_loader/` | Renamed to `rules_loader/` |
| `.claude/config.yml` | Added `rules_loader` section |
| `.claude/hooks/rules_loader/config.json` | Updated paths, renamed keys |
| `.claude/hooks/rules_loader/src/__main__.py` | Added config check logic |
| `.claude/hooks/rules_loader/src/paths.py` | Updated path resolution, added config.yml reading |
| `.claude/hooks/rules_loader/src/loader.py` | Renamed functions, added filter logic |
| `.claude/settings.json` | Updated hook command paths |
| `.claude/README.md` | Updated structure section |

## TODO

- [x] Create `.claude/rules/` directory
- [x] Move all directive files from `directives/` to `rules/`
- [x] Delete empty `directives/` directory
- [x] Rename `hooks/directive_loader/` → `hooks/rules_loader/`
- [x] Add `rules_loader` section to `config.yml`
- [x] Update `hooks/rules_loader/config.json` (paths, key names)
- [x] Rename functions in `hooks/rules_loader/src/loader.py`
- [x] Modify `hooks/rules_loader/src/__main__.py` with config check
- [x] Update `hooks/rules_loader/src/paths.py` for config.yml reading
- [x] Update `settings.json` hook command paths
- [x] Update `README.md` structure section
- [ ] Test rules_loader hook
- [ ] Commit and push changes
