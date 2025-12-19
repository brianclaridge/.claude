# Phase 3: Remaining Improvements Catalog

**Generated:** 2025-12-19
**Status:** Backlog - Pending Prioritization
**Source:** bright-dazzling-pearl.md (completed Phase 1+2)

---

## Summary

27 remaining issues from the original improvement catalog. These are medium and low priority items that can be addressed incrementally.

---

## Medium Priority Issues (15)

### 21. Regex Compilation in Loops ✅
**File:** `/workspace/.claude/skills/git-manager/scripts/message.py:111-122`
**Status:** FIXED - Pre-compiled SCOPE_PATTERNS at module level.

### 22. Inconsistent Rule Formatting ✅
**Pattern:** Rules 000-040 use plain text; 050, 090, 095 use code blocks.
**Status:** DOCUMENTED - Accepted as intentional (plain for short rules, code blocks for complex).

### 23. Vague "Factual" Definition ✅
**File:** `/workspace/.claude/rules/010-session-starter.md:45-46`
**Status:** FIXED - Added explicit definition of factual vs non-factual content.

### 24. Missing Config Module ✅
**File:** `/workspace/.claude/hooks/session_context_injector/src/__main__.py:8`
**Status:** VERIFIED - Module exists and works correctly.

### 25. Inconsistent Error Return Codes ✅
**Pattern:** Different skills return different codes for similar errors.
**Status:** DOCUMENTED - Exit code convention in skills/README.md.

### 26. Missing Docstrings
**Pattern:** Some complex functions lack documentation.
**Status:** DEFERRED - Low impact, address incrementally.

### 27. Missing Import in discovery.py ✅
**File:** `/workspace/.claude/skills/aws-login/lib/discovery.py`
**Status:** FIXED - Added missing `import os`.

### 28. Hardcoded Pricing Data
**Pattern:** Version-specific AWS pricing data in code.
**Status:** DEFERRED - Requires external data source design.

### 29. Missing Config Validation (gomplate-manager) ✅
**File:** `/workspace/.claude/skills/gomplate-manager/`
**Status:** FIXED - Added pydantic schema in scripts/schemas.py.

### 30. Model Inefficiency ✅
**File:** `/workspace/.claude/agents/hello-world.md`
**Status:** FIXED - Changed from opus to haiku.

### 31. Potential Unused AWS Util Imports
**File:** `/workspace/.claude/lib/aws_utils/`
**Status:** DEFERRED - Requires comprehensive import analysis.

### 32. Double-Failure Error Logging
**Pattern:** Some error handlers log then re-raise, causing duplicate logs.
**Status:** DEFERRED - Needs case-by-case review.

### 33. Missing Type Hints
**Pattern:** Some utility functions lack type annotations.
**Status:** DEFERRED - Low priority, address incrementally.

### 34. Inconsistent Naming Conventions
**Pattern:** Mixed snake_case/camelCase in some modules.
**Status:** DEFERRED - Would require extensive refactoring.

### 35. Additional Medium Issues
- Missing __all__ exports in __init__.py files
- Inconsistent log message formatting
**Status:** DEFERRED - Minor cosmetic issues.

---

## Low Priority Issues (12)

### 36. Add Pre-commit Hooks ✅
**Status:** DONE - Created `.pre-commit-config.yaml` with ruff, markdownlint, shellcheck.

### 37. Create Shared Utilities Library ✅
**Status:** DONE - lib/subprocess_helper created and documented.

### 38. Document Agent Color Scheme ✅
**Status:** DONE - Added to agents/_template.md with color table.

### 39. Add Tests for Hook Scripts
**Status:** DEFERRED - Requires test infrastructure setup.

### 40. Create Config Schema Files ✅
**Status:** DONE - Pydantic schemas for 4 hooks (3 prior + gomplate-manager).

### 41. Standardize Exit Code Semantics ✅
**Status:** DONE - Documented in skills/README.md.

### 42. Update Pricing Data Mechanism
**Status:** DEFERRED - Requires external data source design.

### 43. Add Type Stubs for External Deps
**Status:** DEFERRED - Low priority.

### 44. Improve Error Messages
**Status:** DEFERRED - Address case-by-case.

### 45. Add Validation for Rule File Format
**Status:** DEFERRED - Would require new tooling.

### 46. Create Agent Template ✅
**Status:** DONE - Created `agents/_template.md` with all fields documented.

### 47. Document Skill Development Guide ✅
**Status:** DONE - Enhanced `skills/README.md` with Python patterns.

---

## Implementation Notes

These items should be addressed based on:
1. **Impact:** How much they improve reliability/maintainability
2. **Effort:** Time required to implement
3. **Dependencies:** Whether they block other work

Recommended approach: Pick 2-3 items per session as cleanup tasks.
