---
id: electron-react
name: Electron + React + TypeScript
tags: [typescript, react, electron, desktop, sqlite, tailwind]
complexity: intermediate
use_cases: [desktop-apps, editors, utilities, dashboards]
---

## Frontend (Renderer Process)

- **React 19** - UI framework with concurrent features
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Accessible, unstyled component primitives
- **Vite HMR** - Fast hot module replacement via electron-vite

## Backend (Main Process)

- **Node.js** - Full Node.js API access
- **Electron 33+** - Chromium + Node.js runtime
- **better-sqlite3** - Synchronous, fast SQLite bindings
- **electron-log** - Structured logging for main/renderer
- **IPC Handlers** - Type-safe inter-process communication

## DevOps

- **electron-vite** - Next-generation Vite-based build tool
- **electron-builder** - Cross-platform packaging (Windows, macOS, Linux)
- **electron-rebuild** - Native module compilation
- **TypeScript** - Shared types between main/renderer

## Stack Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Electron | Active, mature | Powers VS Code, Slack, Discord |
| React | Dominant | Largest ecosystem, excellent tooling |
| electron-vite | Active, modern | Fastest Electron build tool |
| electron-builder | Industry standard | 13k+ GitHub stars, proven |
| better-sqlite3 | Stable | Fastest Node.js SQLite bindings |
| Tailwind CSS | Ubiquitous | Default choice for modern apps |

## Rationale

Electron remains the dominant cross-platform desktop framework, powering applications like VS Code, Slack, Discord, and Figma. This stack combines Electron with modern React 19 and the fastest available build tooling (electron-vite).

**Best for**: Desktop applications requiring rich UI, native OS integration, and offline-first capabilities.

**Security model**: Context isolation enabled by default. Renderer process sandboxed. All Node.js access via preload scripts with `contextBridge`. Never enable `nodeIntegration`.

**Performance considerations**: Main process handles CPU-intensive tasks and database operations. Use web workers in renderer for heavy computations. Lazy-load large assets.

**Hiring**: Large JavaScript/TypeScript talent pool. React skills transfer directly.

## Modern Alternatives

- **Tauri** - Rust-based, smaller binaries, uses system webview (not Chromium)
- **Neutralino.js** - Lightweight, uses system webview
- **Wails** - Go-based alternative to Electron
- **Flutter Desktop** - Dart-based, single codebase for mobile/desktop

## Bootstrap

### Files Generated

- `package.json` - Dependencies and scripts
- `electron.vite.config.ts` - Build configuration
- `electron-builder.yml` - Packaging configuration
- `tsconfig.json` - TypeScript configuration
- `tsconfig.node.json` - Node.js TypeScript config
- `tsconfig.web.json` - Web TypeScript config
- `tailwind.config.ts` - Tailwind configuration
- `postcss.config.js` - PostCSS configuration
- `src/main/index.ts` - Main process entry
- `src/preload/index.ts` - Preload script (contextBridge)
- `src/renderer/index.html` - Renderer HTML
- `src/renderer/App.tsx` - Root React component
- `src/shared/types.ts` - Shared type definitions

### Commands

```bash
# Initialize project with electron-vite React template
npm create electron-vite@latest my-app -- --template react-ts
cd my-app

# Install core dependencies
npm install better-sqlite3 electron-log
npm install -D @types/better-sqlite3 electron-rebuild

# Rebuild native modules for Electron
npx electron-rebuild -f -w better-sqlite3

# Install UI dependencies
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install shadcn/ui (interactive setup)
npx shadcn@latest init

# Development (with HMR)
npm run dev

# Build application
npm run build

# Preview built application
npm run preview

# Package for current platform
npm run build && npm exec electron-builder

# Package for all platforms
npm run build && npm exec electron-builder --mac --win --linux
```

### Directory Structure

```text
project/
├── src/
│   ├── main/                     # Main process (Node.js)
│   │   ├── index.ts              # Entry point, window creation
│   │   ├── ipc/                  # IPC channel handlers
│   │   │   └── handlers.ts       # Type-safe IPC handlers
│   │   └── services/             # Business logic
│   │       └── database.ts       # SQLite operations
│   ├── preload/                  # Preload scripts
│   │   └── index.ts              # contextBridge API exposure
│   ├── renderer/                 # Renderer process (React)
│   │   ├── index.html            # HTML entry
│   │   ├── main.tsx              # React entry
│   │   ├── App.tsx               # Root component
│   │   ├── components/           # UI components
│   │   │   └── ui/               # shadcn/ui components
│   │   ├── lib/                  # Utilities
│   │   └── styles/               # CSS/Tailwind
│   │       └── globals.css
│   └── shared/                   # Shared between processes
│       └── types.ts              # IPC message types
├── resources/                    # App icons and assets
│   └── icon.png
├── electron.vite.config.ts       # electron-vite config
├── electron-builder.yml          # Packaging config
├── package.json
├── tsconfig.json                 # Base TypeScript config
├── tsconfig.node.json            # Main/preload config
├── tsconfig.web.json             # Renderer config
├── tailwind.config.ts
├── postcss.config.js
└── components.json               # shadcn/ui config
```

### Security Configuration

```typescript
// src/main/index.ts - BrowserWindow creation
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,     // REQUIRED: Isolate renderer context
    nodeIntegration: false,     // REQUIRED: Disable Node in renderer
    sandbox: true,              // RECOMMENDED: Enable sandbox
    preload: path.join(__dirname, '../preload/index.js')
  }
})
```

```typescript
// src/preload/index.ts - Safe API exposure
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  // Expose specific, validated functions only
  getVersion: () => ipcRenderer.invoke('get-version'),
  queryDatabase: (sql: string) => ipcRenderer.invoke('db:query', sql),
  onUpdateAvailable: (callback: () => void) =>
    ipcRenderer.on('update-available', callback)
})
```

### Type-Safe IPC Pattern

```typescript
// src/shared/types.ts
export interface ElectronAPI {
  getVersion: () => Promise<string>
  queryDatabase: (sql: string) => Promise<unknown[]>
  onUpdateAvailable: (callback: () => void) => void
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}
```
