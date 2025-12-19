# stack-manager Agent

> Recommend and bootstrap application stacks.

## Overview

Analyzes requirements and recommends appropriate application stacks. Can bootstrap new projects with selected stack.

## Invocation

```
/stack-manager
```

Or triggered by:
- "suggest a stack"
- "what stack should I use"
- "bootstrap project"
- "scaffold app"

## Available Stacks

| Stack | Language | Use Case |
|-------|----------|----------|
| htmx-fastapi | Python | Server-rendered apps |
| nextjs-prisma | TypeScript | SaaS, e-commerce |
| django-htmx | Python | Admin panels |
| go-templ-htmx | Go | High-performance APIs |
| sveltekit-supabase | TypeScript | MVPs, real-time |
| vue-vite-fastapi | Python/TS | Data apps |

## Workflow

1. Gather requirements (project type, scale, team skills)
2. Analyze constraints
3. Recommend matching stacks
4. Bootstrap selected stack (optional)

## Skills Used

- `stack-manager` - Stack selection and bootstrap

## Source

[agents/stack-manager.md](../../agents/stack-manager.md)

## See Also

- [Stacks Documentation](../stacks/README.md)
