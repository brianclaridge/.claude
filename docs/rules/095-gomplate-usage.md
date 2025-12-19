# Rule 095: gomplate-usage

> gomplate template best practices from docs.gomplate.ca.

## Priority

Domain-specific (050-099)

## Directive

Follow official gomplate best practices. All templates must work in Linux container environment.

## Key Requirements

### Configuration File
Use `gomplate.yaml` for all configuration
```yaml
inputFiles:
  - templates/app.json.tmpl
outputFiles:
  - /etc/app/config.json
```

### Environment Access
**Always use `.Env.VAR`** for fail-fast behavior
```go
# Correct - Fails if VAR unset
{{ .Env.WORKSPACE_PATH }}

# Wrong - Silent empty string
{{ getenv "OPTIONAL_VAR" }}
```

### Whitespace
**Spaces inside delimiters**
```go
# Correct
{{ .Env.VAR }}
{{- .Env.VAR -}}

# Wrong
{{.Env.VAR}}
```

### Output Paths
**Absolute paths** for container destinations
```yaml
# Correct
outputFiles:
  - /root/.config/app.json

# Wrong
outputFiles:
  - ./config/app.json
```

### JSON Templates
Validate structure
```json
{
  "apiKey": "{{ .Env.API_KEY }}",
  "timeout": 30
}
```

## Validation

Use `/gomplate` or gomplate-manager agent.

## Source

[rules/095-gomplate-usage.md](../../rules/095-gomplate-usage.md)
