---
id: htmx-fastapi
name: HTMX + FastAPI
tags: [python, htmx, fastapi, server-rendered, jinja2]
complexity: intermediate
use_cases: [web-apps, dashboards, admin-panels, media-apps]
---

## Frontend

- **HTMX** - Dynamic interactions without JavaScript frameworks
- **Jinja2 templates** - Server-side rendering with partials
- **CSS custom properties** - Theming support (dark mode, etc.)
- **Alpine.js** (optional) - Light client-side interactivity

## Backend

- **Python 3.12+** - Runtime
- **FastAPI** - Async API framework with automatic OpenAPI docs
- **Pydantic** - Request/response validation and data models
- **Loguru** - Structured logging with rotation
- **PyYAML** - Configuration management

## DevOps

- **Docker + Docker Compose** - Containerized deployment
- **uv (Astral)** - Fast Python package management
- **Taskfile** - Task runner for build/dev/test workflows

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI | Active, growing | Released 2018, dominant Python API framework |
| HTMX | Active, gaining traction | 2020 revival of hypermedia, production-ready |
| Jinja2 | Mature, stable | Battle-tested since 2008, extremely reliable |
| Docker | Ubiquitous | Standard containerization |
| uv | New, high momentum | 2024 release, rapidly becoming preferred Python toolchain |

## Rationale

This stack prioritizes simplicity and server-side rendering. HTMX enables dynamic interactions without JavaScript frameworks, keeping the frontend as HTML partials rendered by Jinja2. FastAPI provides a modern async Python backend with automatic OpenAPI docs and Pydantic validation.

**Best for**: Teams wanting Python backend with minimal frontend complexity. Ideal for dashboards, admin panels, and content-heavy applications.

**Example project**: [FFmpeg Sandbox](https://github.com/brianclaridge/FFmpeg-sandbox) - Media processing app using this stack.

## Modern Alternatives

- Swap HTMX for **Inertia.js** with React/Vue for richer interactivity
- Use **Litestar** instead of FastAPI for better performance
- Consider **Templ** (Go) for type-safe templates if moving to Go

## Bootstrap

### Files Generated

- `pyproject.toml` - Python project configuration with uv
- `Dockerfile` - Multi-stage Python container
- `docker-compose.yml` - Development environment
- `Taskfile.yml` - Task runner commands
- `src/main.py` - FastAPI application entry
- `src/templates/base.html` - Jinja2 base template
- `src/static/css/main.css` - CSS with custom properties
- `.env.example` - Environment variables template

### Commands

```bash
# Initialize project
uv init --name my-app
uv add fastapi uvicorn jinja2 python-multipart loguru pyyaml

# Development
uv run uvicorn src.main:app --reload

# Docker
docker compose up --build
```

### Directory Structure

```text
project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   └── __init__.py
│   ├── templates/
│   │   ├── base.html
│   │   └── partials/
│   └── static/
│       ├── css/
│       └── js/
├── tests/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── Taskfile.yml
└── .env.example
```
