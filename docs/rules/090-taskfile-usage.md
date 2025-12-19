# Rule 090: taskfile-usage

> Taskfile.yml best practices.

## Priority

Domain-specific (050-099)

## Directive

Follow official Taskfile best practices from taskfile.dev. All Taskfiles must work cross-platform.

## Key Rules

### Variables
```yaml
# Correct - UPPERCASE
vars:
  BINARY_NAME: myapp

# Wrong - lowercase
vars:
  binary_name: myapp
```

### Template Syntax
```yaml
# Correct - No whitespace
cmd: echo {{.BINARY_NAME}}

# Wrong - Whitespace
cmd: echo {{ .BINARY_NAME }}
```

### Task Naming
```yaml
# Correct - kebab-case, colon namespaces
tasks:
  build-app:
  docker:build:

# Wrong
tasks:
  buildApp:
  docker_build:
```

### Required Fields
```yaml
tasks:
  build:
    desc: Build the application
    aliases: [b]
    silent: true
    cmds:
      - go build
```

### Cross-Platform
Use `pwsh` for cross-platform commands or `platforms:` directive.

## Source

[rules/090-taskfile-usage.md](../../rules/090-taskfile-usage.md)
