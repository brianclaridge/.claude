---
id: vue-vite-fastapi
name: Vue 3 + Vite + FastAPI
tags: [python, typescript, vue, fastapi, vite, postgresql]
complexity: intermediate
use_cases: [data-apps, dashboards, internal-tools, enterprise]
---

## Frontend

- **Vue 3** - Composition API with reactivity
- **Vite** - Lightning-fast build tool
- **TypeScript** - Type-safe JavaScript
- **Pinia** - State management
- **Tailwind CSS** or **PrimeVue** - Styling

## Backend

- **Python 3.12+** - Runtime
- **FastAPI** - Async API framework with OpenAPI
- **Pydantic** - Request/response validation
- **SQLAlchemy** or **SQLModel** - ORM
- **PostgreSQL** - Database

## DevOps

- **Docker + Docker Compose** - Development and deployment
- **uv (Astral)** - Python package management
- **pnpm** - Frontend package management

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Vue 3 | Mature, active | Strong ecosystem, excellent docs |
| Vite | Active, growing | Created by Vue author, fast builds |
| FastAPI | Active, growing | Dominant Python API framework |
| Pinia | Active | Official Vue state management |
| SQLModel | Active | FastAPI-compatible ORM by same author |

## Rationale

Vue 3 offers a gentler learning curve than React while providing excellent TypeScript support. Paired with FastAPI on the backend, you get end-to-end type safety with automatic OpenAPI generation. This stack is popular in enterprise and data-heavy applications.

**Best for**: Data visualization, dashboards, internal tools, enterprise applications. Teams with Python backend expertise wanting modern frontend.

**Hiring**: Large Vue talent pool, especially in enterprise. Python devs can contribute to full stack.

## Modern Alternatives

- Use **Nuxt 3** for server-side rendering
- Consider **tRPC + Vue Query** for end-to-end type safety
- Swap FastAPI for **Litestar** for better performance

## Bootstrap

### Files Generated

- `frontend/package.json` - Vue/Vite dependencies
- `frontend/vite.config.ts` - Vite configuration
- `backend/pyproject.toml` - Python dependencies
- `docker-compose.yml` - Full stack development
- `.env.example` - Environment variables

### Commands

```bash
# Initialize frontend
pnpm create vite frontend --template vue-ts
cd frontend
pnpm add pinia vue-router @tanstack/vue-query
pnpm add -D tailwindcss postcss autoprefixer

# Initialize backend
cd ../backend
uv init --name backend
uv add fastapi uvicorn sqlmodel psycopg loguru

# Development (both)
docker compose up --build

# Or separately
cd frontend && pnpm dev
cd backend && uv run uvicorn main:app --reload
```

### Directory Structure

```text
project/
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── components/
│   │   ├── stores/
│   │   └── views/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── routes/
│   └── pyproject.toml
├── docker-compose.yml
├── Dockerfile.frontend
├── Dockerfile.backend
└── .env.example
```
