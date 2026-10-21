# RUEXIS AI — Electron App (Desktop Container)

Native Electron 43 desktop application container that coordinates the transparent mascot overlay window, the React control panel, Win32 desktop integration, and child process lifecycle for the backend server.

---

## ⚡ Quick Start

```bash
cd frontend/electron_app

# Install dependencies
npm install

# Start Electron
# In development: loads Vite dev server at http://localhost:5173
# In production: loads compiled bundle at ../renderer/dist/index.html
npm start
```

### Available Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| `npm start` | `electron .` | Launches the desktop container |
| `npm run rebuild` | `electron-rebuild` | Rebuilds native C++ modules (`koffi`, etc.) for Electron ABI |
| `npm run pack` | `electron-builder --dir` | Generates unpacked standalone executable directory |
| `npm run dist` | `electron-builder` | Produces production Windows installer (.exe) |

---

## 📁 Directory Structure

```
electron_app/
├── package.json                  # Electron & native module dependencies + packaging scripts
├── mascot_transitions.json       # State machine transition table for mascot animations
├── test_mascot.html              # Standalone mascot animation test page
└── src/
    ├── main.js                   # Main process: window management, IPC, backend spawn, DPI
    ├── preload.js                # Context bridge: exposes window.mascotAPI to renderer
    ├── mascot.html               # Mascot overlay window HTML shell & ZZZ stage
    ├── mascot.css                # Mascot window styles, positioning, and animation keyframes
    ├── mascot.js                 # Mascot renderer: canvas sprite engine & state machine
    └── assets/                   # Character sprite sheet directories (4 characters × 13 animations)
        ├── mr_nerdy/
        ├── ms_nerdy/
        ├── mr_nerd/
        └── ms_nerd/
```

---

## 🏗️ Window Architecture

The application manages two coordinated `BrowserWindow` instances:

```
┌────────────────────────────────────────────────────────────────────────┐
│  BrowserWindow: Panel (Control Hub)                                    │
│  Loads: http://localhost:5173 (Dev) | ../renderer/dist/index.html (Prod)│
│  Mode 1 (Docked): 340×480 px, floating, lockstep drag with mascot      │
│  Mode 2 (Maximized): Fullscreen workspace (min 800×600 px), mascot hid │
│  Shortcut: CommandOrControl+Shift+P                                    │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│  BrowserWindow: Mascot (Overlay)                                       │
│  Loads: src/mascot.html                                                │
│  Size: 125×150 px (scaled by monitor DPI) — frameless, always-on-top   │
│  Features: transparent canvas, click-through passthrough with hover    │
│            hitbox, Win32 taskbar avoidance via Koffi FFI               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Main Process Subsystems (`src/main.js`)

### 1. Backend Auto-Spawn & Health Poller
- Checks if the FastAPI backend is running on `http://localhost:8000`.
- If absent, attempts to find python in the local virtual environment (`.venv/Scripts/python.exe` or `backend/venv`) or falls back to system `python`, launching `backend/main.py`.
- Gracefully kills the backend child process on `app.on('will-quit')`.

### 2. Taskbar & Display DPI Detection
- Uses **Koffi C FFI** to call Win32 `SHAppBarMessage` (`shell32.dll`) to detect taskbar location (bottom, top, left, right) and screen boundaries.
- Adjusts window dimensions and coordinates dynamically when displays or scaling factors change (`screen.on('display-metrics-changed')`).

### 3. Lockstep Dragging
- When the user drags the mascot window, `drag-window` IPC events calculate position deltas and move both the mascot and the docked control panel in synchronized lockstep.

### 4. Active Window Context Polling
- Uses `active-win` to inspect the focused OS window. If an academic paper or PDF viewer is detected in foreground focus, the mascot automatically transitions to the `reading` state.

---

## 📡 IPC API Reference (`preload.js`)

All communication between the React renderer and the Electron main process is securely routed through `contextBridge` as `window.mascotAPI`:

### Renderer → Main (`ipcRenderer.send`)

| Channel | Payload | Description |
|---------|---------|-------------|
| `set-ignore-mouse-events` | `(ignore, options)` | Toggles click-through passthrough on the mascot window |
| `drag-window` | `{deltaX, deltaY}` | Moves mascot & docked panel window in lockstep |
| `drag-end` | — | Signals completion of a window drag operation |
| `toggle-panel` | — | Toggles visibility of the sidebar control panel |
| `toggle-maximize` | — | Toggles between docked (340×480) and maximized workspace |
| `upload-pdf` | `{filePath, type, modelName}` | Copies file to uploads and triggers pipeline execution |
| `open-file-selector` | `(type, modelName)` | Opens native file dialog and stages file without running |
| `trigger-upload` | `{filename, filePath, type, modelName}` | Triggers pipeline execution for a staged file |
| `set-mascot-state` | `state: string` | Sets mascot animation pose (idle, hunch, excited, etc.) |
| `set-mascot-skin` | `skinId: string` | Changes active mascot skin (`mr_nerdy`, `ms_nerdy`, etc.) |
| `user-activity` | — | Resets mascot idle timer on user keyboard/mouse events |

### Main → Renderer (`webContents.send`)

| Channel | Payload | Description |
|---------|---------|-------------|
| `upload-status` | `{success, filename, type, filePath}` | Result of file copy and pipeline kickoff |
| `file-staged` | `{success, filename, type, filePath, modelName}` | Staged file notification for chat attachments |
| `pipeline-log` | `{text}` | Live pipeline progress log line forwarded from SSE |
| `pipeline-completed` | `{success, filename, reportContent?, error?}` | Pipeline execution completion payload |
| `state-change` | `state: string` | Instructs mascot canvas to transition pose |
| `maximize-change` | `isMaximized: boolean` | Informs renderer of window maximization state |
| `mascot-skin-change` | `skinId: string` | Informs mascot canvas of active character skin |

### Renderer → Main (Invoke / Handle)

| Channel | Returns | Description |
|---------|---------|-------------|
| `get-mascot-skin` | `skinId: string` | Returns active skin preference from `electron-store` |

---

## 🎭 Mascot Sprite Engine (`src/mascot.js`)

- **Rendering:** Standalone HTML5 Canvas 2D engine with zero React dependency.
- **Hub Routing:** All pose sequences transition through frame 0 (`standing/idle`) as an intermediate hub.
- **Alpha Blending:** Eliminates frame stutter via a 130ms 6-step cross-fading routine.
- **Character Skins:** Supports 4 skins: `mr_nerdy`, `ms_nerdy`, `mr_nerd`, and `ms_nerd`.
- **Animations:** 13 states including `idle`, `hunch` (typing/working), `excite` (done), `angry` (error), `wave` (greeting), `sleep`, and `catching`.

---

## 📦 Native Modules & Packaging

- **`koffi`**: Win32 C FFI binding for taskbar placement. Must be unpacked outside of the ASAR archive in `electron-builder`:
  ```json
  "build": {
    "asarUnpack": ["**/*.node"]
  }
  ```
- **`active-win`**: Active foreground window detection.
- **`electron-store`**: Persistent user settings and mascot skin storage.

---

## 🔗 Related Documentation

- [Frontend Overview](../README.md) — High-level dual-window architecture and design tokens.
- [React Renderer Guide](../renderer/README.md) — React 19 UI components, Zustand stores, and build setup.
