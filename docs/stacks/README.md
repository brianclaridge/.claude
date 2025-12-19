# Stacks

Application stack templates for bootstrapping new projects via `/stack-manager`.

## Overview

Stacks are markdown files in `stacks/` that define complete application architectures. The stack-manager agent recommends stacks based on requirements and can bootstrap projects.

## Available Stacks

| Stack | Language | Best For |
|-------|----------|----------|
| [htmx-fastapi](htmx-fastapi.md) | Python | Server-rendered apps, dashboards |
| [nextjs-prisma](nextjs-prisma.md) | TypeScript | SaaS, e-commerce, content sites |
| [django-htmx](django-htmx.md) | Python | Admin panels, rapid prototyping |
| [go-templ-htmx](go-templ-htmx.md) | Go | High-performance APIs, microservices |
| [sveltekit-supabase](sveltekit-supabase.md) | TypeScript | MVPs, real-time apps |
| [vue-vite-fastapi](vue-vite-fastapi.md) | Python/TS | Data apps, dashboards |

## Stack Comparison

### By Performance

| Stack | Cold Start | Response Time | Memory |
|-------|------------|---------------|--------|
| go-templ-htmx | Fast | Fastest | Low |
| htmx-fastapi | Medium | Fast | Medium |
| django-htmx | Slow | Medium | High |
| nextjs-prisma | Slow | Medium | High |
| sveltekit-supabase | Medium | Fast | Medium |
| vue-vite-fastapi | Medium | Fast | Medium |

### By Use Case

| Use Case | Recommended Stack |
|----------|-------------------|
| Admin dashboard | django-htmx |
| SaaS application | nextjs-prisma |
| Real-time features | sveltekit-supabase |
| High-traffic API | go-templ-htmx |
| Data visualization | vue-vite-fastapi |
| Simple web app | htmx-fastapi |

### By Learning Curve

| Stack | Complexity |
|-------|------------|
| htmx-fastapi | Beginner |
| django-htmx | Beginner |
| sveltekit-supabase | Intermediate |
| vue-vite-fastapi | Intermediate |
| nextjs-prisma | Intermediate |
| go-templ-htmx | Advanced |

## Using Stacks

### Get Recommendations

```
User: /stack-manager
Claude: What type of application are you building?
[Interactive selection...]
Claude: Based on your requirements, I recommend htmx-fastapi because...
```

### Bootstrap Project

```
User: Bootstrap the htmx-fastapi stack
Claude: [Creates project structure, installs dependencies, configures environment]
```

## Stack Structure

Each stack definition includes:

```markdown
# Stack Name

> One-line description

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | ... |
| Backend | ... |
| Database | ... |

## Use Cases

Best suited for...

## Project Structure

```text
project/
├── ...
```

## Getting Started

Setup commands...

## Configuration

Environment variables...
```

## Creating New Stacks

See [Development Guide](../DEVELOPMENT.md#creating-stacks).

## See Also

- [stack-manager Skill](../skills/stack-manager.md)
- [Development](../DEVELOPMENT.md) - Extension guide
