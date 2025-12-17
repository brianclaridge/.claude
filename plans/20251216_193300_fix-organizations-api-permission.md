# Plan: Fix Organizations API Permission Issue

## Problem

The SSO auto-discovery picks the first account returned by `sso.list_accounts()`, but that account (`client-dev2`) doesn't have Organizations API permissions. Only the management account can call `ListRoots`.

```
Using account provision-iam-client-dev2 to query Organizations...
AccessDeniedException: You don't have permissions to access this resource.
```

## Root Cause

Line 137 in `__main__.py`:
```python
first_account = sso_accounts[0]  # Random account, not management
```

## Solution: Interactive Account Selection for Organizations Query

Present user with a list of discovered accounts and let them select which one to use for Organizations API queries (typically the management account).

### New Flow

1. SSO device auth → get access token
2. List available accounts via SSO
3. **NEW**: Ask user to select which account has Organizations permissions
4. Use selected account to query Organizations API
5. Continue with profile creation

### Implementation

#### Option A: Always Ask User (Simple)
```python
# Present numbered list of accounts
logger.info("Select account with Organizations permissions:")
for i, acc in enumerate(sso_accounts):
    logger.info(f"  {i+1}. {acc.account_name} ({acc.account_id})")

# Use InquirerPy for selection
selected = inquirer.fuzzy(
    message="Select management account:",
    choices=[acc.account_name for acc in sso_accounts],
).execute()
```

#### Option B: Smart Heuristic + Fallback (Preferred)
1. Look for accounts with "manager", "management", "master", "root" in name
2. If found, try those first
3. If fails or not found, ask user to select

### Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/aws-login/lib/__main__.py` | Add `_find_management_account()` helper with heuristics + user selection fallback |

## Implementation Steps

1. Add `_select_management_account()` helper function:
   - Sort accounts by management-related naming patterns first
   - Patterns: "manager", "management", "master", "root" (case-insensitive)
   - If match found, try that account first
   - If Organizations API fails, fallback to user selection

2. Add `_try_organizations_query()` helper:
   - Attempts Organizations API with given account
   - Returns (success, tree) tuple
   - Catches AccessDeniedException gracefully

3. Update `first_run_setup()`:
   - Replace lines 136-161 with call to new helpers
   - Loop: try heuristic account → if fails → ask user to select → retry

4. Use InquirerPy for fallback selection (already imported elsewhere)

## Heuristic Priority Order

```python
MANAGEMENT_PATTERNS = [
    "root",         # root-account
    "main",         # main-account
    "manager",      # provision-iam-manager
    "management",   # management-account
]
```

## Fallback Selection UI

```python
from InquirerPy import inquirer

def _ask_user_to_select_management_account(accounts):
    choices = [
        {"name": f"{acc.account_name} ({acc.account_id})", "value": acc}
        for acc in accounts
    ]
    return inquirer.fuzzy(
        message="Select the management account (has Organizations permissions):",
        choices=choices,
    ).execute()
```
