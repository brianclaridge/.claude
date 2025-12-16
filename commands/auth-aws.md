Authenticate to AWS using SSO.

Invoke the aws-login skill to:
1. Check for existing valid credentials
2. If expired/missing, initiate SSO login
3. Detect and present the SSO URL and device code
4. Verify authentication after completion
