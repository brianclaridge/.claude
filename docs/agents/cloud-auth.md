# cloud-auth Agent

> Cloud provider authentication for AWS and GCP.

## Overview

Handles authentication to cloud providers via SSO or application default credentials. Supports AWS Identity Center and GCP.

## Invocation

```
/cloud-auth
```

Or triggered by:
- "login to AWS"
- "login to GCP"
- "authenticate to cloud"

## Capabilities

- AWS SSO device authorization
- GCP Application Default Credentials
- Profile management
- Token caching

## Skills Used

- `aws-login` - AWS SSO authentication
- `gcp-login` - GCP authentication

## Configuration

Environment variables in `.env`:

```bash
# AWS
AWS_SSO_START_URL="https://your-org.awsapps.com/start"
AWS_SSO_REGION="us-west-2"

# GCP (optional)
GOOGLE_CLOUD_PROJECT="your-project"
```

## Source

[agents/cloud-auth.md](../../agents/cloud-auth.md)
