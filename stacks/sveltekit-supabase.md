---
id: sveltekit-supabase
name: SvelteKit + Supabase
tags: [typescript, svelte, sveltekit, supabase, serverless, postgresql]
complexity: beginner
use_cases: [mvps, startups, real-time-apps, rapid-prototyping]
---

## Frontend

- **SvelteKit** - Full-stack Svelte framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Svelte 5** - Runes-based reactivity

## Backend

- **Supabase** - Firebase alternative (PostgreSQL-based)
- **Supabase Auth** - Built-in authentication
- **Supabase Realtime** - WebSocket subscriptions
- **Row Level Security** - Database-level authorization

## DevOps

- **Vercel / Netlify** - Edge deployment
- **pnpm** - Fast package manager
- **Docker** (optional) - Local Supabase

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| SvelteKit | Active, growing | Fastest-growing JS framework, excellent DX |
| Supabase | Active, growing | Open-source Firebase alternative |
| Tailwind CSS | Ubiquitous | Default styling choice |
| TypeScript | Industry standard | Microsoft-backed |

## Rationale

SvelteKit offers the best developer experience with minimal boilerplate and excellent performance. Supabase provides a complete backend-as-a-service with PostgreSQL, auth, storage, and real-time subscriptions. Together, they enable rapid development with minimal infrastructure management.

**Best for**: MVPs, startups, hackathons, real-time applications. Teams wanting fast iteration with minimal ops burden.

**Hiring**: Growing pool, Svelte attracts modern developers.

## Modern Alternatives

- Use **Drizzle ORM** for more control over database queries
- Consider **Lucia Auth** for self-hosted authentication
- Swap Supabase for **PocketBase** for simpler single-binary backend

## Bootstrap

### Files Generated

- `package.json` - Dependencies and scripts
- `svelte.config.js` - SvelteKit configuration
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.ts` - Tailwind configuration
- `.env.example` - Supabase credentials template

### Commands

```bash
# Initialize project
pnpm create svelte@latest my-app
cd my-app
pnpm add @supabase/supabase-js @supabase/ssr
pnpm add -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Development
pnpm dev

# Supabase (local)
npx supabase init
npx supabase start

# Build
pnpm build
```

### Directory Structure

```text
project/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte
│   │   ├── +page.svelte
│   │   └── api/
│   ├── lib/
│   │   ├── supabase.ts
│   │   └── components/
│   └── app.html
├── static/
├── supabase/
│   ├── config.toml
│   └── migrations/
├── package.json
├── svelte.config.js
├── tsconfig.json
├── tailwind.config.ts
└── .env.example
```
