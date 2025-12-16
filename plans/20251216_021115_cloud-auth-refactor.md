# Plan: Cloud Auth Refactor - Separate Slash Commands with SSO URL Detection

## Objective

Replace the single `/cloud-auth` command with provider-specific commands:
- `/auth-aws` → invokes `aws-login` skill with SSO URL detection
- `/auth-gcp` → invokes `gcp-login` skill with auth URL detection

## Current State

| Component | Location | Status |
|-----------|----------|--------|
| `/cloud-auth` command | `.claude/commands/cloud-auth.md` | To be removed |
| `cloud-auth` agent | `.claude/agents/cloud-auth.md` | To be removed |
| `aws-login` skill | `.claude/skills/aws-login/` | Enhance with URL detection |
| `gcp-login` skill | `.claude/skills/gcp-login/` | Enhance with URL detection |

## Implementation Plan

### Phase 1: Create Slash Commands

#### `/auth-aws` Command

**File**: `.claude/commands/auth-aws.md`

```markdown
Authenticate to AWS using SSO.

Invoke the aws-login skill to:
1. Check for existing valid credentials
2. If expired/missing, initiate SSO login
3. Detect and present the SSO URL and device code
4. Verify authentication after completion
```

#### `/auth-gcp` Command

**File**: `.claude/commands/auth-gcp.md`

```markdown
Authenticate to Google Cloud Platform.

Invoke the gcp-login skill to:
1. Check for existing valid credentials
2. If expired/missing, initiate gcloud auth login
3. Detect and present the auth URL and code
4. Verify authentication after completion
```

### Phase 2: Enhance AWS Login Skill - SSO URL Detection

**File to modify**: `.claude/skills/aws-login/scripts/cli/sso_login.py`

**Current behavior** (line 210-214):
```python
result = subprocess.run(
    ['aws', 'sso', 'login', '--profile', profile_name, '--no-browser'],
    check=False
)
```
- Runs interactively, output goes directly to terminal
- No capture of URL/code

**New behavior**:
```python
import re

SSO_URL_PATTERN = r"(https://[\w.-]+\.awsapps\.com/start[^\s]*)"
DEVICE_CODE_PATTERN = r"([A-Z]{4}-[A-Z]{4})"

def run_sso_login(profile_name: str) -> dict:
    """Run SSO login and capture URL/code for presentation."""
    process = subprocess.Popen(
        ['aws', 'sso', 'login', '--profile', profile_name, '--no-browser'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    sso_url = None
    device_code = None

    for line in process.stdout:
        output_lines.append(line)
        print(line, end='')  # Still show to user

        # Detect SSO URL
        url_match = re.search(SSO_URL_PATTERN, line)
        if url_match:
            sso_url = url_match.group(1)

        # Detect device code
        code_match = re.search(DEVICE_CODE_PATTERN, line)
        if code_match:
            device_code = code_match.group(1)

    process.wait()

    return {
        "success": process.returncode == 0,
        "sso_url": sso_url,
        "device_code": device_code,
        "output": "".join(output_lines)
    }

def format_sso_prompt(sso_url: str, device_code: str) -> str:
    """Format SSO URL and code for user presentation."""
    return f"""
**AWS SSO Authentication Required**

| Field | Value |
|-------|-------|
| URL | {sso_url} |
| Code | **{device_code}** |

Open the URL in your browser and enter the code to authenticate.
"""
```

### Phase 3: Enhance GCP Login Skill - Auth URL Detection

**File to modify**: `.claude/skills/gcp-login/scripts/auth.py`

**Current behavior** (line 113-132):
```python
result = subprocess.run(cmd)  # Interactive, no capture
```

**New behavior**:
```python
import re

GCP_URL_PATTERN = r"(https://accounts\.google\.com/o/oauth2/auth[^\s]*)"
GCP_CODE_PATTERN = r"Enter the following code[:\s]+([A-Z0-9-]+)"

def login_with_adc(no_browser: bool = True) -> dict:
    """Run gcloud auth and capture URL/code for presentation."""
    cmd = ["gcloud", "auth", "login", "--update-adc"]
    if no_browser:
        cmd.append("--no-launch-browser")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    auth_url = None
    auth_code = None

    for line in process.stdout:
        output_lines.append(line)
        print(line, end='')

        url_match = re.search(GCP_URL_PATTERN, line)
        if url_match:
            auth_url = url_match.group(1)

        code_match = re.search(GCP_CODE_PATTERN, line)
        if code_match:
            auth_code = code_match.group(1)

    process.wait()

    return {
        "success": process.returncode == 0,
        "auth_url": auth_url,
        "auth_code": auth_code,
        "output": "".join(output_lines)
    }

def format_gcp_prompt(auth_url: str, auth_code: str = None) -> str:
    """Format GCP auth URL for user presentation."""
    code_row = f"| Code | **{auth_code}** |" if auth_code else ""
    return f"""
**GCP Authentication Required**

| Field | Value |
|-------|-------|
| URL | {auth_url} |
{code_row}

Open the URL in your browser to authenticate.
"""
```

### Phase 4: Update Skill Documentation

**File**: `.claude/skills/aws-login/SKILL.md`
- Document SSO URL detection feature
- Update usage examples

**File**: `.claude/skills/gcp-login/SKILL.md`
- Document auth URL detection feature
- Update usage examples

### Phase 5: Remove Deprecated Components

| File | Action |
|------|--------|
| `.claude/commands/cloud-auth.md` | Delete |
| `.claude/agents/cloud-auth.md` | Delete |
| `.claude/hooks/cloud_auth_prompt/` | Delete (no longer needed) |

### Phase 6: Update Configuration

**File**: `.claude/config.yml`

Remove or disable cloud auth prompt hook:
```yaml
cloud_providers:
  aws:
    enabled: true
    display_name: "AWS"
    description: "Amazon Web Services SSO"
    config_file: .aws.yml
    prompt_at_start: false  # Changed: no auto-prompt

  gcp:
    enabled: true
    display_name: "GCP"
    description: "Google Cloud Platform"
    prompt_at_start: false  # Changed: no auto-prompt
```

## Files to Create/Modify/Delete

| File | Action | Purpose |
|------|--------|---------|
| `.claude/commands/auth-aws.md` | Create | AWS auth slash command |
| `.claude/commands/auth-gcp.md` | Create | GCP auth slash command |
| `.claude/skills/aws-login/scripts/cli/sso_login.py` | Modify | Add URL detection |
| `.claude/skills/gcp-login/scripts/auth.py` | Modify | Add URL detection |
| `.claude/skills/aws-login/SKILL.md` | Modify | Update docs |
| `.claude/skills/gcp-login/SKILL.md` | Modify | Update docs |
| `.claude/commands/cloud-auth.md` | Delete | Deprecated |
| `.claude/agents/cloud-auth.md` | Delete | Deprecated |
| `.claude/hooks/cloud_auth_prompt/` | Delete | No longer needed |
| `.claude/config.yml` | Modify | Disable prompt_at_start |
| `.claude/skills/aws-login/scripts/core/config_reader.py` | Modify | Use `${CLAUDE_DATA_PATH}/.aws.yml` path |
| `.claude/skills/aws-login/scripts/config/aws_config_helper.py` | Modify | First-run root login flow |

### Phase 7: AWS Config File Path and First-Run Flow

**Requirement**: First-time setup requires root login, config stored at `${CLAUDE_DATA_PATH}/.aws.yml`

**File to modify**: `.claude/skills/aws-login/scripts/core/config_reader.py`

**Changes**:
1. Config file path: `${CLAUDE_DATA_PATH}/.aws.yml` (not project-local)
2. First-run flow:
   - Detect missing config file
   - Prompt user to authenticate to root account first
   - After root auth, run Organizations discovery
   - Generate `.aws.yml` with discovered accounts
   - Save to `${CLAUDE_DATA_PATH}/.aws.yml`

**First-Run Flow**:
```python
import os

CONFIG_PATH = os.path.join(os.environ.get("CLAUDE_DATA_PATH", "."), ".aws.yml")

def get_config_path() -> str:
    """Get AWS config file path."""
    return CONFIG_PATH

def config_exists() -> bool:
    """Check if config file exists."""
    return os.path.exists(CONFIG_PATH)

def first_run_setup() -> None:
    """First-time setup flow."""
    logger.info("No AWS config found. Starting first-run setup...")

    # Step 1: Prompt for root account SSO login
    logger.info("Please authenticate to your AWS root/management account first.")
    root_profile = create_root_profile()  # Creates temp profile for root login

    # Step 2: Run SSO login for root
    result = run_sso_login(root_profile)
    if not result["success"]:
        raise RuntimeError("Root account authentication failed")

    # Step 3: Discover accounts from Organizations
    accounts = discover_accounts_from_organizations()

    # Step 4: Generate and save config
    config = generate_config(accounts)
    save_config(config, CONFIG_PATH)

    logger.info(f"AWS config saved to {CONFIG_PATH}")
```

**File to modify**: `.claude/skills/aws-login/scripts/config/aws_config_helper.py`
- Update profile paths to use new config location
- Update any hardcoded `.aws.yml` references

## Testing Strategy

1. **First-run `/auth-aws`** (no existing config):
   - Remove `${CLAUDE_DATA_PATH}/.aws.yml` if exists
   - Run `/auth-aws`
   - Verify prompts for root account SSO login
   - Verify SSO URL and device code are presented
   - Complete root auth
   - Verify Organizations discovery runs
   - Verify `.aws.yml` created at `${CLAUDE_DATA_PATH}/.aws.yml`

2. **Subsequent `/auth-aws`** (config exists):
   - Run `/auth-aws`
   - Verify loads existing config
   - Verify account selection menu appears
   - Verify SSO URL and device code are presented
   - Complete authentication
   - Verify credentials work

3. **Manual test `/auth-gcp`**:
   - Run `/auth-gcp`
   - Verify auth URL is detected and displayed
   - Complete authentication
   - Verify credentials work

4. **Regression check**:
   - Ensure old `/cloud-auth` no longer exists
   - Verify session start no longer prompts for cloud auth
