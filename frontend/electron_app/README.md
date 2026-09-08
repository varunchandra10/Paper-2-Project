# RUEXIS AI — Electron App (Desktop Container)

Native Electron 43 desktop application that wraps the React renderer and manages the interactive mascot overlay window. This is the top-level executable that the user launches to run the full RUEXIS AI platform.

---

## Quick Start

```bash
cd frontend/electron_app

# Install dependencies
npm install

# Start Electron (requires the renderer build to exist at ../renderer/dist/)
# and the backend to be running at http://localhost:8000
npm start
```

> **Development workflow:** Run `npm run dev` in `frontend/renderer` first (Vite dev server at 5173), then `npm start` here. The main process auto-spawns the Python backend as a child process if it is not already running.

---

## Directory Structure

```
electron_app/
├── package.json                  # Electron + native module dependencies
├── mascot_transitions.json       # State machine transition table for mascot animations
├── test_mascot.html              # Standalone mascot animation test page
└── src/
    ├── main.js                   # Main process: window management, IPC, backend spawn
    ├── preload.js                 # Context bridge: exposes mascotAPI to renderer
    ├── mascot.html               # Mascot overlay window HTML shell
    ├── mascot.js                 # Mascot renderer: sprite animation engine, state machine
    ├── mascot.css                # Mascot window styles
    └── assets/                   # Mascot sprite sheet images (4 characters × 13 animations)
        ├── mr_nerdy/
        ├── ms_nerdy/
        ├── mr_nerd/
        └── ms_nerd/
```

---

## Architecture Overview

The app creates **two Electron windows** with distinct responsibilities:

```
┌─────────────────────────────────────────────────────────┐
│  BrowserWindow: Panel (main app)                         │
│  Loads: ../renderer/dist/index.html (production)         │
│       : http://localhost:5173     (dev server)           │
│  Size: 1100×900 — resizable, standard chrome             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  BrowserWindow: Mascot (overlay)                         │
│  Loads: src/mascot.html                                  │
│  Size: 125×150 (DPI-scaled) — frameless, always-on-top   │
│  Features: transparent, click-through passthrough        │
│            positioned bottom-right of work area          │
└─────────────────────────────────────────────────────────┘
```

---

## Main Process — `src/main.js`

### Backend Auto-Spawn

On startup, the main process checks if the Python FastAPI backend is already listening on port 8000. If not, it spawns `python main.py` as a child process using `spawn()`. The backend process is managed and killed on app quit.

### Window Management

| Function | Description |
|----------|-------------|
| `createPanelWindow()` | Creates the main 1100×900 `BrowserWindow` loading the renderer |
| `createMascotWindow()` | Creates the 125×150 transparent overlay for the mascot character |
| `positionMascotDefault()` | Positions mascot bottom-right of the workArea (taskbar-aware) |
| `getTaskbarPosition()` | Win32 `SHAppBarMessage` call via Koffi FFI to detect taskbar position/edge |

### DPI & Multi-Monitor Support

- The mascot window size is scaled by `nearestDisplay.scaleFactor` to appear correctly on HiDPI displays.
- `screen.on('display-metrics-changed')` re-positions the mascot when the display configuration changes (resolution, scale factor, monitor connect/disconnect).
- `currentDisplayId` tracks which monitor the mascot is on so position corrections only fire on relevant display changes.

### Backend Spawn & Health Check

```
App Ready
    │
    ▼
checkBackendReady() — polls http://localhost:8000 every 500ms, up to 60s
    │  If not already running:
    ▼
spawn('python main.py') as backendProcess
    │
    ▼
On success: createPanelWindow() + createMascotWindow()
On timeout: show error dialog
```

---

## IPC Channel Reference

All IPC channels are bridged securely via `preload.js` using `contextBridge.exposeInMainWorld('mascotAPI', {...})`.

### Renderer → Main (`ipcRenderer.send`)

| Channel | Payload | Description |
|---------|---------|-------------|
| `set-ignore-mouse-events` | `(ignore, options)` | Enables/disables click-through on the mascot window |
| `drag-window` | `{deltaX, deltaY}` | Moves the mascot window by delta (custom borderless drag) |
| `drag-end` | — | Signals drag completion |
| `toggle-panel` | — | Show/hide the main panel window |
| `toggle-maximize` | — | Toggle maximize state of the panel |
| `upload-pdf` | `{filePath, type, modelName}` | Copy file to uploads/ and immediately run the pipeline |
| `open-file-selector` | `(type, modelName)` | Open native file dialog, stage file WITHOUT running pipeline |
| `trigger-upload` | `{filename, filePath, type, modelName}` | Run the pipeline for an already-staged file |
| `set-mascot-state` | `state: string` | Programmatically change mascot animation state |
| `user-activity` | — | Report user interaction to reset idle timer |
| `set-mascot-skin` | `skinId: string` | Switch mascot character (mr_nerdy / ms_nerdy / mr_nerd / ms_nerd) |

### Main → Renderer (`webContents.send`)

| Channel | Payload | Description |
|---------|---------|-------------|
| `upload-status` | `{success, filename, type, filePath}` | File copy result after `upload-pdf` |
| `file-staged` | `{success, filename, type, filePath, modelName}` | File staged result after `open-file-selector` |
| `selected-file` | file data | Native file selection result |
| `pipeline-log` | `{text}` | Live pipeline progress log line |
| `pipeline-completed` | `{success, filename, reportContent?, error?}` | Pipeline job finished |
| `state-change` | `state: string` | Mascot state change signal |
| `maximize-change` | `isMaximized: boolean` | Panel window maximize state change |
| `mascot-skin-change` | `skinId: string` | Notify mascot renderer to switch character |
| `user-activity` | — | Forward activity signal to mascot |

### Renderer → Main (invoke / reply)

| Channel | Returns | Description |
|---------|---------|-------------|
| `get-mascot-skin` | `skinId: string` | Retrieve currently active mascot skin from electron-store |

---

## Mascot Window — `src/mascot.js`

The mascot overlay is a standalone HTML+Canvas renderer with no React dependency.

### Four Characters

| ID | Sprite Folder | Style |
|----|--------------|-------|
| `mr_nerdy` | `assets/mr_nerdy/` | Classic academic nerd |
| `ms_nerdy` | `assets/ms_nerdy/` | Female academic variant |
| `mr_nerd` | `assets/mr_nerd/` | Compact nerd |
| `ms_nerd` | `assets/ms_nerd/` | Compact female variant |

Each character has **13 animation states** (3-frame sprite sheets unless noted):

| State | Frames | Trigger |
|-------|--------|---------|
| `sleep` | 3 | Idle timeout (long inactivity) |
| `excite` | 3 | Pipeline completed successfully |
| `angry` | 3 | Pipeline/upload error |
| `hunch` | 3 | Working / generating chat response |
| `wave` | 3 | App startup greeting |
| `blink` | 3 | Random idle micro-animation |
| `catching` | 3 | File staged for upload |
| `thinking` | 3 | ReACT thought/tool execution |
| `tired` | 3 | Extended work session |
| `having_sipping` | 3 | Coffee sip during long operations |
| `confused` | 3 | Error / unexpected response |
| `peeking` | 3 | Transition to idle from edge |
| `standing` | 1 | Default idle rest state |

### State Machine

The mascot runs a **finite state machine** driven by `mascot_transitions.json`. State transitions are triggered by:

1. **Backend pipeline events** — `pipeline-log` SSE signals emit `mascot-state` events directly into the mascot window via IPC.
2. **Chat activity** — The panel renderer calls `window.mascotAPI.setMascotState(state)` via preload when chat is generating, done, or errored.
3. **User interaction** — Mouse hover, click, drag events on the mascot hitbox.
4. **Idle timer** — Activity timeout after ~3 minutes transitions to `tired` → `sleep`.

### Sprite Rendering

Sprites are rendered on a `<canvas>` element using the Canvas 2D API:
- Each animation loads a horizontal sprite sheet (N frames × sprite width)
- Frames advance on a `setInterval` timer (configurable fps per state)
- On state change, the current animation is cancelled and the new sprite sheet is loaded

### Click-Through & Drag

- The mascot window is `transparent`, `alwaysOnTop`, and normally passes all mouse events through to the desktop (`setIgnoreMouseEvents(true, { forward: true })`).
- On `mouseenter` of the hitbox, mouse events are captured (`setIgnoreMouseEvents(false)`) so the user can interact.
- **Click** (no drag movement) → `togglePanel()` — shows/hides the main app window.
- **Drag** (movement > 5px threshold) → `dragWindow({deltaX, deltaY})` — moves the overlay around the screen.

---

## Skin Persistence

The currently active mascot character is persisted via `electron-store` (a JSON file in the Electron user data directory). On app launch, the stored `skinId` is restored and sent to the mascot renderer via `mascot-skin-change` IPC.

---

## Pipeline Integration

When a PDF is uploaded via the mascot (drag-drop or file selector):

```
User drops PDF on mascot
    │
    ▼
mascotAPI.uploadPDF(filePath, type, modelName)
    │  (IPC: upload-pdf)
    ▼
main.js: copy file to uploads/, set mascot state → 'reading'
    │
    ▼
runPipelineOrchestrator(filename, destPath, type, modelName)
    │  POST /upload to backend
    │  SSE stream: /stream/{run_id}
    ▼
pipeline-log events → forwarded to panel via webContents.send
mascot-state signals → sendMascotState(state)
    │
    ▼
On complete: mascot → 'excited' (3.5s) → 'idle'
             panel ← pipeline-completed event
```

The **staged upload** flow (`open-file-selector` + `trigger-upload`) follows the same path but delays pipeline execution until the user explicitly sends a message with the attachment in the chat input.

---

## Native Modules

| Module | Purpose |
|--------|---------|
| `koffi` | Win32 FFI bindings for `SHAppBarMessage` (taskbar position detection) |
| `active-win` | Active window detection for idle state tracking |
| `electron-store` | Persistent JSON key-value store for mascot skin preference |

All native modules have graceful fallbacks — if `koffi` or `active-win` fail to load (e.g., on non-Windows), the app uses Electron's built-in `workArea` for positioning.

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `electron` 43 | Desktop application runtime |
| `electron-store` 11 | Persistent settings storage |
| `koffi` 3 | Native Win32 C FFI (taskbar detection) |
| `active-win` 8 | Active application window tracking |
| `electron-builder` | Production packaging (dev dep) |
