---
id: django-htmx
name: Django + HTMX
tags: [python, django, htmx, postgresql, server-rendered]
complexity: beginner
use_cases: [admin-panels, internal-tools, content-platforms, rapid-prototyping]
---

## Frontend

- **HTMX** - Dynamic interactions without JavaScript frameworks
- **Django Templates** - Native templating with inheritance
- **Alpine.js** (optional) - Light client-side interactivity
- **django-htmx** - HTMX integration utilities

## Backend

- **Python 3.12+** - Runtime
- **Django 5.x** - Batteries-included web framework
- **Django ORM** - Built-in database abstraction
- **PostgreSQL** - Production database
- **Celery** (optional) - Async task queue

## DevOps

- **Docker + Docker Compose** - Containerized deployment
- **uv (Astral)** - Fast Python package management
- **Gunicorn** - Production WSGI server

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Django | Mature, active | 19+ years, excellent stability and docs |
| HTMX | Active, growing | Modern hypermedia, Django-friendly |
| PostgreSQL | Rock-solid | Industry standard |
| Celery | Mature | De facto async task solution |
| uv | New, high momentum | 2024, rapidly replacing pip/poetry |

## Rationale

Django's "batteries included" philosophy means everything works out of the box: admin panel, authentication, ORM, migrations, forms. Adding HTMX modernizes the frontend without abandoning Django's server-rendered model.

**Best for**: Rapid prototyping, internal tools, content management, admin-heavy applications. Teams wanting convention over configuration.

**Hiring**: Large Python talent pool, Django is well-known and respected.

## Modern Alternatives

- Use **Django Ninja** for FastAPI-style API views
- Consider **Wagtail** for CMS functionality
- Swap to **Litestar** if Django's ORM overhead is too heavy

## Bootstrap

### Files Generated

- `pyproject.toml` - Python project with uv
- `manage.py` - Django management script
- `config/settings.py` - Django settings
- `Dockerfile` - Multi-stage Python container
- `docker-compose.yml` - Development environment
- `.env.example` - Environment variables

### Commands

```bash
# Initialize project
uv init --name my-app
uv add django django-htmx psycopg gunicorn whitenoise

# Create Django project
uv run django-admin startproject config .
uv run python manage.py startapp core

# Development
uv run python manage.py runserver

# Database
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Docker
docker compose up --build
```

### Directory Structure

```text
project/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── core/
├── templates/
│   └── base.html
├── static/
├── manage.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
