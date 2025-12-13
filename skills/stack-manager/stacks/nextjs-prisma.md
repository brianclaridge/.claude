---
id: nextjs-prisma
name: Next.js + TypeScript + Prisma
tags: [typescript, react, nextjs, prisma, postgresql, tailwind]
complexity: intermediate
use_cases: [saas, dashboards, e-commerce, content-sites]
---

## Frontend

- **Next.js 14+ (App Router)** - React meta-framework with SSR/SSG
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Server Components** - Server-first rendering model

## Backend

- **Next.js API Routes** - Integrated backend
- **Prisma** - Type-safe ORM with migrations
- **PostgreSQL** - Relational database
- **NextAuth.js** (optional) - Authentication

## DevOps

- **Docker + Docker Compose** - Local development
- **Vercel** - Native deployment platform
- **pnpm** - Fast, disk-efficient package manager

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Next.js | Active, dominant | Vercel-backed, largest React framework |
| TypeScript | Industry standard | Microsoft-backed, widespread adoption |
| Prisma | Active, growing | Type-safe ORM, excellent DX |
| Tailwind CSS | Ubiquitous | Default choice for modern apps |
| PostgreSQL | Rock-solid | Industry standard relational DB |

## Rationale

This is the dominant React meta-framework stack. Next.js provides the best React developer experience with built-in routing, SSR, and API routes. Prisma adds type-safe database access that integrates perfectly with TypeScript. Tailwind CSS has become the default styling choice.

**Best for**: SaaS products, e-commerce, content platforms, and teams already comfortable with React.

**Hiring**: Extremely easy - largest JavaScript/TypeScript talent pool.

## Modern Alternatives

- Use **tRPC** instead of REST API routes for end-to-end type safety
- Consider **Drizzle ORM** for lighter-weight alternative to Prisma
- Swap PostgreSQL for **PlanetScale** (serverless MySQL) for simpler scaling

## Bootstrap

### Files Generated

- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `next.config.js` - Next.js configuration
- `tailwind.config.ts` - Tailwind configuration
- `prisma/schema.prisma` - Database schema
- `Dockerfile` - Production container
- `docker-compose.yml` - Development environment
- `.env.example` - Environment variables

### Commands

```bash
# Initialize project
pnpm create next-app@latest my-app --typescript --tailwind --app --src-dir
cd my-app
pnpm add prisma @prisma/client
pnpm prisma init

# Development
pnpm dev

# Database
pnpm prisma migrate dev
pnpm prisma studio

# Docker
docker compose up --build
```

### Directory Structure

```text
project/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── api/
│   ├── components/
│   └── lib/
│       └── prisma.ts
├── prisma/
│   └── schema.prisma
├── public/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
