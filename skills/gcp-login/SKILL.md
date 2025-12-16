---
name: gcp-login
description: Authenticate to Google Cloud Platform using Application Default Credentials. Use when user selects GCP from cloud provider selection, or says "login to GCP", "gcloud auth", "authenticate to Google Cloud".
allowed-tools: Bash, Read, AskUserQuestion
---

# GCP Login Skill

Authenticate to Google Cloud Platform using `gcloud auth login --update-adc`.

## Activation Triggers

- `/auth-gcp` slash command invokes this skill
- User says: "login to GCP", "gcloud auth", "authenticate to GCP"
- User explicitly invokes: "use the gcp-login skill"

## Prerequisites

- `gcloud` CLI installed and in PATH
- Environment variable `GOOGLE_CLOUD_PROJECT` set (optional, for quota project)

## Workflow

### Step 1: Check Environment

```bash
# Verify gcloud is available
which gcloud || echo "gcloud not found"

# Check current auth status
gcloud auth list 2>/dev/null || echo "No active accounts"
```

If gcloud not found:
- Inform user: "gcloud CLI not found. Please install Google Cloud SDK."
- Exit workflow

### Step 2: Set Project Configuration

If `GOOGLE_CLOUD_PROJECT` environment variable is set:

```bash
gcloud config set project "${GOOGLE_CLOUD_PROJECT}"
gcloud auth application-default set-quota-project "${GOOGLE_CLOUD_PROJECT}"
```

If not set:
- Inform user the project will need to be set manually
- Continue to authentication

### Step 3: Authenticate

Run authentication with device code flow (no browser launch in container):

```bash
uv run --directory ${CLAUDE_SKILLS_PATH}/gcp-login python scripts/auth.py
```

**Auth URL Detection**: The skill automatically detects and presents the authentication URL:

| Field | Value |
|-------|-------|
| URL | https://accounts.google.com/o/oauth2/auth?... |

User actions:
1. Open the URL in a browser
2. Complete authentication in browser

Wait for authentication to complete (command will block until done).

### Step 4: Verify Authentication

After authentication completes:

```bash
gcloud auth list
gcloud config get-value project
```

Report to user:
- Active account email
- Current project (if set)

### Step 5: Optional Bucket Policy (Advanced)

If environment variable `GENMEDIA_BUCKET` is set and user needs storage access:

Use AskUserQuestion:

```json
{
  "question": "Add IAM policy binding for storage bucket access?",
  "header": "Storage",
  "options": [
    {"label": "Yes", "description": "Grant storage.objectUser role on gs://${GENMEDIA_BUCKET}"},
    {"label": "No", "description": "Skip bucket policy setup"}
  ],
  "multiSelect": false
}
```

If yes:

```bash
gcloud storage buckets add-iam-policy-binding "gs://${GENMEDIA_BUCKET}" \
  --member="user:${GCLOUD_EMAIL_ADDRESS}" \
  --role="roles/storage.objectUser"
```

## Error Handling

| Error | Resolution |
|-------|------------|
| gcloud not found | Inform user to install Google Cloud SDK |
| Auth timeout | Offer to retry authentication |
| No project set | Warn user, continue anyway |
| Bucket policy fails | Report error, authentication still valid |

## Safety Rules

**NEVER**:
- Store credentials directly
- Log authentication tokens
- Run commands that could revoke existing credentials

**ALWAYS**:
- Use `--no-launch-browser` in containerized environments
- Verify authentication success before reporting
- Allow user to skip optional steps

## Example Flow

```text
User: login to GCP

Claude: Checking GCP environment...
        gcloud CLI: Found
        Current auth: None
        Project: my-project-id

Claude: Starting GCP authentication...
        Please open this URL in your browser:
        https://accounts.google.com/o/oauth2/auth?...

        Enter this code: XXXX-XXXX

        Waiting for authentication...

Claude: GCP authentication successful!
        Account: user@example.com
        Project: my-project-id
```
