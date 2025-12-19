# gcp-login Skill

> GCP authentication via Application Default Credentials.

## Overview

Handles Google Cloud Platform authentication using `gcloud auth application-default login`.

## Activation Triggers

- "login to GCP"
- "gcloud auth"
- "authenticate to Google Cloud"
- cloud-auth agent invocation

## Workflow

1. Check existing credentials
2. Run `gcloud auth application-default login`
3. User completes browser authentication
4. Verify credentials

## Configuration

Optional in `.env`:
```bash
GOOGLE_CLOUD_PROJECT="your-project-id"
```

## Source

[skills/gcp-login/README.md](../../skills/gcp-login/README.md)
