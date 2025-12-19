# Troubleshooting

Common issues and solutions for the .claude environment.

## Docker Issues

### Container Won't Start

**Symptom**: `task claude` fails to start container.

**Solutions**:

1. Ensure Docker Desktop is running
2. Check Docker Desktop has file sharing permissions for required paths
3. Verify no port conflicts: `docker ps -a`
4. Try rebuilding: `task claude:build`

### Bind Mount Errors

**Symptom**: "Error response from daemon: invalid mount config"

**Solution**: Add paths to Docker Desktop → Settings → Resources → File Sharing:
- `${HOME_SSH_PATH}`
- `${CLAUDE_ROOT_PATH}`
- `${CLAUDE_PARENT_DIR}`

### Docker Socket Permission Denied

**Symptom**: "permission denied while trying to connect to Docker daemon"

**Solution**:
```bash
# Linux
sudo chmod 666 /var/run/docker.sock

# macOS - check Docker Desktop is running
```

## AWS SSO Issues

### SSO Login Failed

**Symptom**: "SSO login failed for profile"

**Solutions**:

1. Verify `AWS_SSO_START_URL` in `.env` is correct
2. Verify `AWS_SSO_REGION` matches your Identity Center region
3. Check network connectivity to AWS

### Wrong Region for SSO

**Symptom**: Device authorization fails or hangs

**Solution**: Set `AWS_SSO_REGION` in `.env` to the region where AWS Identity Center is configured (e.g., `us-west-2`).

## Git Issues

### Index.lock Exists

**Symptom**: "Another git process seems to be running"

**Solution**: The git-manager skill handles this automatically. If manual fix needed:
```bash
rm -f .git/index.lock
rm -f .git/modules/**/index.lock
```

### Git Identity Not Configured

**Symptom**: "Please tell me who you are" during commit

**Solution**: Add to `.env`:
```bash
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="your.email@example.com"
```

Or let git-manager auto-detect from SSH.

## Playwright Issues

### Browser Not Installed

**Symptom**: "Executable doesn't exist at /path/to/browser"

**Solution**:
```bash
npx playwright install chromium
```

### Browser Lock Error

**Symptom**: "Browser is already in use"

**Solution**: The `playwright_healer` hook handles this automatically. If persistent:
```bash
pkill -f chromium
pkill -f chrome
```

## Session Issues

### Project Analysis Fails

**Symptom**: Session start hangs or errors

**Solutions**:

1. Check `.claude/` directory exists and is accessible
2. Verify `settings.json` is valid JSON
3. Check for syntax errors in rules

### Rules Not Loading

**Symptom**: Claude doesn't follow behavioral rules

**Solutions**:

1. Verify `rules/*.md` files exist
2. Check for markdown syntax errors
3. Rules load at session start - restart session

### Hook Errors

**Symptom**: "Hook failed" messages

**Solutions**:

1. Check hook logs in `.data/logs/`
2. Verify hook has valid Python syntax
3. Check dependencies: `uv sync --directory hooks/my-hook`

## MCP Server Issues

### Context7 Not Available

**Symptom**: Library documentation lookup fails

**Solutions**:

1. Verify `CONTEXT7_API_KEY` is set
2. Check network connectivity
3. Verify MCP server configured in `settings.json`

### Playwright MCP Errors

**Symptom**: Browser automation fails

**Solutions**:

1. Check Playwright is installed
2. Verify browser executable exists
3. Check for port conflicts

## Performance Issues

### Slow Session Start

**Symptom**: Long delay before Claude responds

**Solutions**:

1. Reduce `commit_history_limit` in `config.yml`
2. Reduce `recent_limit` for plans
3. Check for large files in workspace

### Context Overflow

**Symptom**: Claude loses track of conversation

**Solution**: This is handled by automatic summarization. For complex tasks:
1. Break into smaller steps
2. Commit frequently to clear context
3. Use plan mode to preserve intent

## Environment Variables

### Missing Variables

**Symptom**: "Environment variable not set" errors

**Solution**: Create `.env` in `.claude/`:
```bash
AWS_SSO_START_URL="https://..."
AWS_SSO_REGION="us-west-2"
AWS_DEFAULT_REGION="us-east-1"
```

### Variables Not Loading

**Symptom**: Variables set but not recognized

**Solutions**:

1. Ensure `.env` is in `.claude/` directory
2. Restart the container
3. Check for syntax errors (no spaces around `=`)

## Getting Help

1. Check logs: `.data/logs/`
2. Run `/health` for environment validation
3. Review [Architecture](ARCHITECTURE.md) for system design
4. Check [Development](DEVELOPMENT.md) for customization

## See Also

- [Setup Guide](SETUP.md) - Initial configuration
- [Architecture](ARCHITECTURE.md) - System design
