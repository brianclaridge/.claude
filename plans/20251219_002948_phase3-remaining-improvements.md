# Phase 3: Remaining Improvements Catalog

**Generated:** 2025-12-19
**Status:** Backlog - Pending Prioritization
**Source:** bright-dazzling-pearl.md (completed Phase 1+2)

---

## Summary

27 remaining issues from the original improvement catalog. These are medium and low priority items that can be addressed incrementally.

---

## Medium Priority Issues (15)

### 21. Regex Compilation in Loops
**File:** `/workspace/.claude/skills/git-manager/scripts/message.py:111-122`
**Issue:** Regex patterns compiled inside loop instead of module level.
**Fix:** Pre-compile patterns at module level for performance.

### 22. Inconsistent Rule Formatting
**Pattern:** Rules 000-040 use plain text; 050, 090, 095 use code blocks.
**Fix:** Establish standard rule format documentation.

### 23. Vague "Factual" Definition
**File:** `/workspace/.claude/rules/010-session-starter.md:45-46`
**Fix:** Define what constitutes "factual" vs "opinion" output.

### 24. Missing Config Module
**File:** `/workspace/.claude/hooks/session_context_injector/src/__main__.py:8`
**Issue:** Imports `.config` - verify module exists.
**Fix:** Verified and working.

### 25. Inconsistent Error Return Codes
**Pattern:** Different skills return different codes for similar errors.
**Fix:** Document standard exit code semantics.

### 26. Missing Docstrings
**Pattern:** Some complex functions lack documentation.
**Fix:** Add docstrings to public functions.

### 27. Unused Imports in discovery.py
**File:** `/workspace/.claude/skills/aws-login/lib/discovery.py`
**Fix:** Remove unused imports.

### 28. Hardcoded Pricing Data
**Pattern:** Version-specific AWS pricing data in code.
**Fix:** Externalize to config or fetch dynamically.

### 29. Missing Config Validation (gomplate-manager)
**File:** `/workspace/.claude/skills/gomplate-manager/`
**Fix:** Add pydantic schema for config validation.

### 30. Model Inefficiency
**File:** `/workspace/.claude/agents/hello-world.md`
**Issue:** Uses opus model for simple hello world.
**Fix:** Change to haiku for efficiency.

### 31. Potential Unused AWS Util Imports
**File:** `/workspace/.claude/lib/aws_utils/`
**Fix:** Audit and remove unused service imports.

### 32. Double-Failure Error Logging
**Pattern:** Some error handlers log then re-raise, causing duplicate logs.
**Fix:** Consolidate error logging patterns.

### 33. Missing Type Hints
**Pattern:** Some utility functions lack type annotations.
**Fix:** Add type hints for public APIs.

### 34. Inconsistent Naming Conventions
**Pattern:** Mixed snake_case/camelCase in some modules.
**Fix:** Standardize to snake_case per Python conventions.

### 35. Additional Medium Issues
- Missing __all__ exports in __init__.py files
- Inconsistent log message formatting

---

## Low Priority Issues (12)

### 36. Add Pre-commit Hooks
**Fix:** Create `.pre-commit-config.yaml` with ruff, mypy checks.

### 37. Create Shared Utilities Library
**Status:** ✅ Partially done (lib/subprocess_helper created).
**Remaining:** Document usage patterns.

### 38. Document Agent Color Scheme
**Fix:** Add color assignment guidelines to agent template.

### 39. Add Tests for Hook Scripts
**Fix:** Create pytest fixtures for hook testing.

### 40. Create Config Schema Files
**Status:** ✅ Done for 3 hooks.
**Remaining:** Document schema patterns.

### 41. Standardize Exit Code Semantics
**Fix:** Document: 0=success, 1=error, 2=needs-input convention.

### 42. Update Pricing Data Mechanism
**Fix:** Create pricing fetcher utility or externalize to config.

### 43. Add Type Stubs for External Deps
**Fix:** Create py.typed markers and stubs as needed.

### 44. Improve Error Messages
**Pattern:** Some errors lack context or actionable guidance.
**Fix:** Review and enhance error messages.

### 45. Add Validation for Rule File Format
**Fix:** Create rule file linter/validator.

### 46. Create Agent Template
**Fix:** Add `.claude/agents/_template.md` with required fields.

### 47. Document Skill Development Guide
**Fix:** Create `skills/README.md` with development guidelines.

---

## Implementation Notes

These items should be addressed based on:
1. **Impact:** How much they improve reliability/maintainability
2. **Effort:** Time required to implement
3. **Dependencies:** Whether they block other work

Recommended approach: Pick 2-3 items per session as cleanup tasks.
