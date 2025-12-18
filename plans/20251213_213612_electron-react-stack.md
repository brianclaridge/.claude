# Plan: Add Electron Desktop Stack to Stack-Manager

## Objective

Add a new "Electron + React" stack option to the stack-manager skill, enabling users to bootstrap VS Code-like desktop applications.

## Research Summary

- **Electron architecture**: Main process (Node.js) + Renderer process (Chromium)
- **Build tool**: electron-vite (fastest, Vite-based, modern)
- **Packaging**: electron-builder (mature, cross-platform)
- **UI**: React 19 + shadcn/ui + Tailwind CSS
- **Database**: SQLite via better-sqlite3 (main process only)
- **Security**: Context isolation, preload scripts, CSP

## File to Create

**Path:** `/workspace/projects/personal/claude-sandbox/.claude/stacks/electron-react.md`

## Stack Definition

### YAML Frontmatter

```yaml
---
id: electron-react
name: Electron + React + TypeScript
tags: [typescript, react, electron, desktop, sqlite, tailwind]
complexity: intermediate
use_cases: [desktop-apps, editors, utilities, dashboards]
---
```

### Sections

| Section | Content |
|---------|---------|
| Frontend | React 19, TypeScript, Tailwind CSS, shadcn/ui |
| Backend (Main Process) | Node.js, Electron, better-sqlite3, electron-log |
| DevOps | electron-vite, electron-builder, Docker (optional) |
| Stack Maturity | Component status table |
| Rationale | Why choose this stack |
| Modern Alternatives | Tauri, Neutralino, alternatives |
| Bootstrap | Files generated, commands, directory structure |

### Directory Structure (Bootstrap Output)

```text
project/
├── src/
│   ├── main/
│   │   ├── index.ts
│   │   ├── ipc/
│   │   └── services/
│   ├── preload/
│   │   └── index.ts
│   ├── renderer/
│   │   ├── index.html
│   │   ├── App.tsx
│   │   └── components/
│   └── shared/
│       └── types.ts
├── electron.vite.config.ts
├── electron-builder.yml
├── package.json
├── tsconfig.json
└── tailwind.config.ts
```

### Bootstrap Commands

```bash
# Initialize with electron-vite template
npm create electron-vite@latest my-app -- --template react-ts
cd my-app

# Add dependencies
npm install better-sqlite3 electron-log
npm install -D @types/better-sqlite3 electron-rebuild

# Add UI dependencies
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn@latest init

# Development
npm run dev

# Build for current platform
npm run build

# Package for distribution
npm run package
```

## Implementation Tasks

- [x] Create physical plan file in .claude/plans/
- [ ] Create `/workspace/projects/personal/claude-sandbox/.claude/stacks/electron-react.md`
- [ ] Follow existing stack format (nextjs-prisma.md as template)
- [ ] Include comprehensive Bootstrap section with electron-vite commands
- [ ] Document security best practices in Rationale section

## Verification

- Stack appears in stack-manager selection
- Tags enable discovery: `typescript`, `react`, `electron`, `desktop`
- Bootstrap commands work on fresh system
