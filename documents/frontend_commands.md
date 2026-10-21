# Frontend Commands & Setup Guide

All essential commands for setting up and running the **RUEXIS AI Frontend** — `electron_app` (desktop container) and `renderer` (React UI).

---

## 1. Project Layout

```
frontend/
├── electron_app/    ← Electron main process, mascot engine, IPC
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── preload.js
│       ├── mascot.js / mascot.html / mascot.css
│       └── assets/  ← Sprite sheets
└── renderer/        ← React 19 + Vite 8 UI
    ├── package.json
    └── src/
```

---

## 2. Renderer Setup

```powershell
cd frontend/renderer

# Install dependencies
npm install

# Start Vite dev server (talks to backend at localhost:8000)
npm run dev
# → http://localhost:5173

# Build production bundle (required before electron_app production run)
npm run build
# → output: frontend/renderer/dist/

# Type-check without building
npm run typecheck

# Preview the production build
npm run preview
```

---

## 3. Electron App Setup

```powershell
cd frontend/electron_app

# Install dependencies (includes koffi, active-win, electron-store)
npm install

# Start Electron (development — connects to Vite dev server at :5173)
# Make sure backend is running first, OR let Electron auto-spawn it from .venv
npm start

# Rebuild native modules (if native module errors after Node/Electron update)
npm run rebuild
# or:
npx electron-rebuild
```

---

## 4. Full Development Startup Sequence

Run each in a separate terminal:

```powershell
# Terminal 1 — Backend
cd backend
venv\Scripts\Activate.ps1
python main.py

# Terminal 2 — Renderer (optional, Electron can load dist/ directly)
cd frontend/renderer
npm run dev

# Terminal 3 — Electron
cd frontend/electron_app
npm start
```

> **Shortcut 1:** If `frontend/renderer/dist/` already exists (from `npm run build`), you can skip Terminal 2. Electron will detect if `:5173` is down and automatically load the production bundle from `dist/index.html`.
>
> **Shortcut 2 (Auto-spawn):** Electron's `main.js` can auto-spawn `backend/main.py` on launch if `<repo>/.venv/Scripts/python.exe` exists or global `python` is on PATH.
>
> **Global Shortcut:** Press `CommandOrControl+Shift+P` (e.g. `Ctrl+Shift+P` on Windows) at any time to toggle the control panel window.

---

## 5. Production Build Sequence

```powershell
# Step 1: Build the React renderer bundle
cd frontend/renderer
npm run build
# → frontend/renderer/dist/index.html

# Step 2: Launch Electron loading the production bundle
cd frontend/electron_app
npm start
```

---

## 6. Native Module Troubleshooting

If `koffi` or `active-win` fail to load after a Node.js or Electron version change:

```powershell
cd frontend/electron_app

# Rebuild all native modules for current Electron version
npm run rebuild
# or direct via npx:
npx electron-rebuild

# Or rebuild specific modules
npx electron-rebuild -f -w koffi
npx electron-rebuild -f -w active-win
```

Verify `koffi` loads correctly:
```powershell
node -e "const koffi = require('koffi'); console.log('koffi OK:', typeof koffi.load)"
```

---

## 7. Dependency Management

### Add a renderer package

```powershell
cd frontend/renderer
npm install <package-name>
```

### Add an Electron package

```powershell
cd frontend/electron_app
npm install <package-name>
```

### Update all packages

```powershell
# Renderer
cd frontend/renderer
npm update

# Electron app
cd frontend/electron_app
npm update
```

---

## 8. Environment Variables (Renderer)

The renderer uses Vite environment variables (prefix `VITE_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000/api/v1` | Override API base URL (browser dev only) |

Set in `frontend/renderer/.env.local` (not committed):

```env
VITE_BACKEND_URL=http://localhost:8000/api/v1
```

> In Electron production the API base is always `http://localhost:8000/api/v1` regardless of env vars — see `src/config/api.ts` → `getApiBase()`.

---

## 9. Key Dev URLs

| URL | Description |
|-----|-------------|
| `http://localhost:5173` | Vite dev server (renderer) |
| `http://localhost:4173` | Vite preview server (`npm run preview`) |
| `http://localhost:5173/` | Panel UI in browser dev mode |
| `http://localhost:8000/docs` | Backend Swagger UI |
| `http://localhost:8000/limits-dashboard` | Live rate limits dashboard |
| `http://localhost:8000/api/status` | Backend JSON health check |

---

## 10. Package Scripts Reference

### `renderer/package.json` scripts

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `vite` | Start Vite dev server at :5173 |
| `build` | `tsc -b && vite build` | TypeScript check + bundle to dist/ |
| `preview` | `vite preview` | Serve production bundle locally at :4173 |
| `typecheck` | `tsc --noEmit` | Type-check only, no output files |
| `lint` | `eslint .` | Run ESLint across renderer source |

### `electron_app/package.json` scripts

| Script | Command | Description |
|--------|---------|-------------|
| `start` | `electron .` | Launch Electron in dev mode |
| `rebuild` | `electron-rebuild` | Rebuild native modules (`koffi`, etc.) |
| `pack` | `electron-builder --dir` | Package desktop app directory (no installer) |
| `dist` | `electron-builder` | Full NSIS Windows installer build |

---

## 11. Connectivity & Smoke Tests

### Verify renderer can reach backend

```powershell
# From renderer/
node -e "fetch('http://localhost:8000/api/status').then(r=>r.json()).then(console.log)"
```

### Check mascotAPI is exposed in Electron

Open DevTools in the panel window (right-click → Inspect) and run:
```javascript
console.log(typeof window.mascotAPI)       // → 'object'
console.log(Object.keys(window.mascotAPI)) // → list of all IPC methods
```

### Check mascot skin persistence

```javascript
// In mascot window DevTools
window.mascotAPI.getMascotSkin().then(skin => console.log('Current skin:', skin))
```

### Check Zustand store state

```javascript
// In panel window DevTools
const store = window.__ZUSTAND_DEVTOOLS__
// Or via React DevTools → Components → panelStore
```

---

## 12. Theme Testing

To quickly cycle through all 4 theme modes in the browser console:

```javascript
// Access themeStore
import { useThemeStore } from './src/store/themeStore'
// Or from DevTools:
useThemeStore.getState().setThemeMode('l1')  // Default light
useThemeStore.getState().setThemeMode('l2')  // Arctic palette
useThemeStore.getState().setThemeMode('l3')  // Iris palette
useThemeStore.getState().setThemeMode('d')   // Dark mode
```
