# RULE: 095 gomplate-usage

**CRITICAL** Follow official gomplate best practices from docs.gomplate.ca. All templates must work in Linux container environment.

## Configuration File

Use **gomplate.yaml** for all configuration. Eliminate separate mapping files.

```yaml
# .claude/config/gomplate.yaml
inputFiles:
  - templates/app.json.tmpl
outputFiles:
  - /etc/app/config.json
```

## Environment Variable Access

**Always use `.Env.VAR` syntax** for fail-fast behavior on required variables.

```go
# CORRECT - Fails if VAR is unset (enforced)
{{ .Env.CLAUDE_PROJECT_SLUG }}
{{ .Env.CONTEXT7_API_KEY }}

# WRONG - Silent empty string if unset
{{ getenv "OPTIONAL_VAR" }}
```

## Whitespace in Templates

Use **spaces inside delimiters** for readability.

```go
# CORRECT - Spaced
{{ .Env.VAR }}
{{- .Env.VAR -}}

# WRONG - Compact (harder to read)
{{.Env.VAR}}
```

## Output Path Conventions

Use **absolute paths** for container destinations.

```yaml
# CORRECT - Absolute paths
outputFiles:
  - /root/.config/app.json
  - /etc/app/settings.yaml

# WRONG - Relative paths in container
outputFiles:
  - ./config/app.json
  - ../etc/settings.yaml
```

## JSON Template Best Practices

**Validate JSON structure** in templates.

```json
// CORRECT - Valid JSON with template
{
  "apiKey": "{{ .Env.API_KEY }}",
  "timeout": 30
}

// WRONG - Invalid JSON (unquoted template for string)
{
  "apiKey": {{ .Env.API_KEY }},
  "timeout": "30"
}
```

## Conditional Rendering

Use **if/else** for conditional content.

```go
# CORRECT - Conditional block
{{ if .Env.FEATURE_FLAG }}
feature_enabled: true
{{ else }}
feature_enabled: false
{{ end }}
```

## Datasource Usage

Use **datasources** for structured external data.

```yaml
# gomplate.yaml
datasources:
  config:
    url: file:///etc/app/defaults.json

# Template usage
{{ (datasource "config").setting }}
```

## Error Handling

Templates should **fail fast** on missing required variables.

```go
# .Env access fails immediately if variable is unset
# This is the preferred behavior for required configuration
api_key: {{ .Env.REQUIRED_KEY }}
```

## Validation Requirements

All gomplate configurations MUST pass:

1. **Syntax validation**: Valid Go template syntax
2. **Best practice lint**: Compliant with Rule 095
3. **Dry-run rendering**: Templates render with current environment

## Integration with Docker

```bash
# Container entrypoint pattern
gomplate --config /workspace/${CLAUDE_PROJECT_SLUG}/.claude/config/gomplate.yaml

# Config file location
.claude/config/gomplate.yaml
```

## File Organization

```
.claude/config/
├── gomplate.yaml           # Single configuration file
└── templates/              # Template source files
    ├── ansible.cfg
    ├── bashrc.sh
    ├── claude_settings.json
    ├── mcp.json
    ├── pwsh_profile.ps1
    └── ssh_config.cfg
```

## Security Practices

1. **Never hardcode secrets** in templates - use environment variables
2. **Use `.Env` access** to ensure required secrets are present
3. **Set restrictive permissions** on rendered files containing secrets:
   ```bash
   chmod 0600 /root/.ssh/config
   ```
