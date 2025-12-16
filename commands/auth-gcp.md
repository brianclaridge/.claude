Authenticate to Google Cloud Platform.

Invoke the gcp-login skill to:
1. Check for existing valid credentials
2. If expired/missing, initiate gcloud auth login
3. Detect and present the auth URL and code
4. Verify authentication after completion
