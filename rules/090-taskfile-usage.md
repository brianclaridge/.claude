# RULE: 090 taskfile-usage

**CRITICAL** Follow official Taskfile best practices from taskfile.dev. All Taskfiles must work cross-platform (host PowerShell and Linux container).

## Variable Naming

**UPPERCASE only** for all variables.

```yaml
# ✓ CORRECT
vars:
  BINARY_NAME: myapp
  BUILD_DIR: ./dist

# ✗ WRONG
vars:
  binary_name: myapp
  build_dir: ./dist
```

## Template Syntax

**No whitespace** around template variables.

```yaml
# ✓ CORRECT
cmd: echo {{.BINARY_NAME}}

# ✗ WRONG
cmd: echo {{ .BINARY_NAME }}
```

## Task Naming

Use **kebab-case** for task names. Use **colon-separated namespaces** for grouping.

```yaml
# ✓ CORRECT
tasks:
  build-app:
  docker:build:
  claude:start:

# ✗ WRONG
tasks:
  buildApp:
  docker_build:
```

## Task Structure

Include **desc:** for all public tasks. Use **aliases:** for common shortcuts. Use **silent: true** by default.

```yaml
tasks:
  build:
    desc: Build the application binary
    aliases: [b]
    silent: true
    cmds:
      - go build -o {{.BINARY_NAME}} .
```

## Cross-Platform Requirements

Use **platforms:** directive for OS-specific commands. Ensure **pwsh** compatibility.

```yaml
tasks:
  clean:
    desc: Clean build artifacts
    platforms: [linux, darwin]
    cmds:
      - rm -rf {{.BUILD_DIR}}

  clean:windows:
    desc: Clean build artifacts (Windows)
    platforms: [windows]
    cmds:
      - pwsh -c "Remove-Item -Recurse -Force {{.BUILD_DIR}}"
```

For cross-platform commands, prefer pwsh which works everywhere:

```yaml
tasks:
  clean:
    desc: Clean build artifacts
    cmds:
      - pwsh -c "Remove-Item -Recurse -Force {{.BUILD_DIR}} -ErrorAction SilentlyContinue"
```

## Script Preference

Prefer **external scripts** for complex logic. Keep Taskfile focused on orchestration.

```yaml
# ✓ CORRECT - External script
tasks:
  deploy:
    desc: Deploy to production
    cmds:
      - pwsh ./scripts/deploy.ps1

# ✗ WRONG - Complex inline logic
tasks:
  deploy:
    cmds:
      - |
        if [ "$ENV" = "prod" ]; then
          docker push ...
          kubectl apply ...
          curl -X POST ...
        fi
```

## Preconditions

Use **preconditions:** for validation before task execution.

```yaml
tasks:
  deploy:
    desc: Deploy application
    preconditions:
      - sh: test -f .env
        msg: ".env file required"
      - sh: which docker
        msg: "Docker not installed"
    cmds:
      - docker compose up -d
```

## Dependencies

Use **deps:** for task dependencies. Use **sources:** and **generates:** for incremental builds.

```yaml
tasks:
  build:
    deps: [lint, test]
    sources:
      - "**/*.go"
    generates:
      - "{{.BUILD_DIR}}/{{.BINARY_NAME}}"
    cmds:
      - go build -o {{.BUILD_DIR}}/{{.BINARY_NAME}} .
```

## Environment Variables

Use **env:** for task-specific environment. Use **dotenv:** for .env file loading.

```yaml
version: '3'

dotenv: ['.env', '.env.local']

tasks:
  run:
    env:
      PORT: 8080
      DEBUG: true
    cmds:
      - go run .
```

## Container Detection

For tasks that behave differently in containers:

```yaml
vars:
  IS_CONTAINER:
    sh: test -f /.dockerenv && echo "true" || echo "false"

tasks:
  setup:
    cmds:
      - task: '{{if eq .IS_CONTAINER "true"}}setup:container{{else}}setup:host{{end}}'
```
