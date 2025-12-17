# Plan: Auto-Detect AWS Management Account

## Problem

The `[profile root]` in `~/.aws/config` is determined solely from `AWS_ROOT_ACCOUNT_ID` env var, which may not match the actual AWS Organizations management account.

## Solution: Eliminate Root Account Env Vars

Use AWS SSO APIs to auto-detect the management account instead of requiring env var configuration.

### New Flow

1. **Bootstrap with SSO only** - Only `AWS_SSO_START_URL` required
2. **Device authorization** - Use `sso-oidc` to get user approval
3. **List available accounts** - Use `sso.list_accounts()` with access token
4. **Authenticate to any account** - User selects from discovered accounts
5. **Query Organizations API** - `describe_organization()` returns `MasterAccountId`
6. **Create root profile** - Point to discovered management account

### Env Var Changes

| Env Var | Current | New |
|---------|---------|-----|
| `AWS_SSO_START_URL` | Required | Required |
| `AWS_DEFAULT_REGION` | Optional | Optional |
| `AWS_ROOT_ACCOUNT_ID` | Required | **REMOVE** |
| `AWS_ROOT_ACCOUNT_NAME` | Required | **REMOVE** |

### Implementation

#### Phase 1: Extract MasterAccountId (Quick Fix)

Modify `organizations.py` to extract and return `MasterAccountId`:

```python
# In discover_organization()
org_response = org.describe_organization()
org_data = org_response.get("Organization", {})
tree["management_account_id"] = org_data.get("MasterAccountId", "")
```

Then validate in `discovery.py` and warn if env var doesn't match.

#### Phase 2: Full Auto-Discovery (Preferred)

1. **New module**: `sso_discovery.py` - Device authorization flow
2. **Update `__main__.py`**: Use discovered accounts list
3. **Update `config.py`**: Make root account env vars optional
4. **Auto-detect root**: Use `MasterAccountId` from Organizations API

### SSO Discovery Flow

```python
# sso_discovery.py
def discover_available_accounts(sso_start_url: str, region: str) -> list[dict]:
    """Use SSO OIDC to discover available accounts without pre-configured profile."""
    sso_oidc = boto3.client('sso-oidc', region_name=region)
    sso = boto3.client('sso', region_name=region)

    # 1. Register client
    client = sso_oidc.register_client(clientName="aws-login", clientType="public")

    # 2. Start device authorization
    auth = sso_oidc.start_device_authorization(
        clientId=client['clientId'],
        clientSecret=client['clientSecret'],
        startUrl=sso_start_url
    )

    # 3. Present verification URI to user
    logger.info(f"Open: {auth['verificationUriComplete']}")
    logger.info(f"Code: {auth['userCode']}")

    # 4. Poll for token (user must approve in browser)
    token = poll_for_token(sso_oidc, client, auth)

    # 5. List available accounts
    accounts = sso.list_accounts(accessToken=token['accessToken'])
    return accounts['accountList']
```

### Files to Modify

| File | Change |
|------|--------|
| `.claude/lib/aws_inspector/aws_inspector/services/organizations.py` | Extract `MasterAccountId` from API response |
| `.claude/skills/aws-login/lib/discovery.py` | Warn if env var doesn't match API value |
| `.claude/skills/aws-login/lib/config.py` | Make `AWS_ROOT_ACCOUNT_ID` optional with fallback |
| `.claude/skills/aws-login/lib/__main__.py` | Use auto-discovered management account |
| `.claude/skills/aws-login/lib/sso_discovery.py` | **NEW**: SSO device auth flow for account discovery |

## Phased Approach

### Phase 1 (This PR): Add validation + warning
- Extract `MasterAccountId` from `describe_organization()`
- Warn if env var doesn't match API
- No breaking changes to existing flow

### Phase 2 (Future): Full auto-discovery
- Implement SSO device authorization flow
- Make root env vars optional
- Auto-detect management account from Organizations API
