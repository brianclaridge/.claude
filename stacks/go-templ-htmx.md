---
id: go-templ-htmx
name: Go + Templ + HTMX
tags: [go, htmx, templ, postgresql, server-rendered, high-performance]
complexity: intermediate
use_cases: [apis, microservices, high-performance-apps, cli-with-web]
---

## Frontend

- **HTMX** - Dynamic interactions without JavaScript frameworks
- **Templ** - Type-safe Go templates (compile-time checked)
- **Tailwind CSS** - Utility-first styling

## Backend

- **Go 1.22+** - Runtime
- **Chi** or **Echo** - Lightweight HTTP routers
- **sqlc** - Type-safe SQL queries
- **PostgreSQL** or **SQLite** - Database

## DevOps

- **Docker** - Single binary deployment
- **Taskfile** - Task runner
- **Air** - Live reload for development

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Go | Mature, growing | Google-backed, excellent performance |
| Templ | Active, new | 2023+, type-safe templates for Go |
| HTMX | Active, growing | Perfect fit for Go's server-rendered model |
| Chi/Echo | Mature | Battle-tested HTTP routers |
| sqlc | Active | Type-safe SQL, growing adoption |

## Rationale

Go's simplicity and performance make it ideal for APIs and microservices. Templ brings type-safe templates that catch errors at compile time, and HTMX provides dynamic UI without JavaScript complexity. The result is a fast, maintainable stack with minimal dependencies.

**Best for**: High-performance APIs, microservices, CLI tools with web interfaces, teams wanting simplicity and speed.

**Hiring**: Go demand is high and growing, talent pool expanding rapidly.

## Modern Alternatives

- Use **Fiber** instead of Chi/Echo for Express-like API
- Consider **Ent** for more feature-rich ORM
- Swap Templ for **gomponents** for functional component approach

## Bootstrap

### Files Generated

- `go.mod` - Go module definition
- `main.go` - Application entry point
- `Dockerfile` - Multi-stage Go container
- `docker-compose.yml` - Development environment
- `Taskfile.yml` - Task runner commands
- `.air.toml` - Live reload configuration

### Commands

```bash
# Initialize project
go mod init my-app
go get github.com/go-chi/chi/v5
go get github.com/a-h/templ/cmd/templ@latest

# Generate templates
templ generate

# Development (with live reload)
air

# Build
go build -o bin/app .

# Docker
docker compose up --build
```

### Directory Structure

```text
project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handlers/
│   │   └── home.go
│   ├── templates/
│   │   ├── base.templ
│   │   └── home.templ
│   └── db/
│       ├── queries.sql
│       └── sqlc.yaml
├── static/
│   └── css/
├── go.mod
├── go.sum
├── Dockerfile
├── docker-compose.yml
├── Taskfile.yml
└── .air.toml
```
