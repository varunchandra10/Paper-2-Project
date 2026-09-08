# 📖 Complete Frontend Reference Guide — RUEXIS AI v2.0

Complete technical breakdown of every module in `frontend/electron_app/src/` and `frontend/renderer/src/`, organized into three sections:

1. **SECTION 1 — File-by-File Explanation** (every key file in both apps)
2. **SECTION 2 — Flow-Based Interaction Breakdown** (all major user flows)
3. **SECTION 3 — Input/Output Specifications per Component**

---

# SECTION 1: File-by-File Explanation

---

## 📁 Electron App (`frontend/electron_app/src/`)

---

### `src/main.js` — Main Process Entry Point

The entire Electron lifecycle lives here. Responsible for window management, backend spawning, IPC handling, and native OS integration.

#### Key Functions

| Function | Description |
|----------|-------------|
| `createPanelWindow()` | Creates 1100×900 `BrowserWindow` loading the React renderer |
| `createMascotWindow()` | Creates 125×150 frameless transparent mascot overlay |
| `positionMascotDefault(display)` | Calculates mascot coordinates from `workArea` + taskbar offset |
| `getTaskbarPosition()` | Win32 `SHAppBarMessage(ABM_GETTASKBARPOS)` via Koffi FFI |
| `checkBackendReady()` | Polls `http://localhost:8000` every 500 ms, up to 60 s |
| `spawnBackend()` | `spawn('python main.py')` in backend/ directory |
| `runPipelineOrchestrator(filename, path, type, model)` | POST /upload → listen SSE stream → forward events to windows |
| `listenToStream(runId, paperTitle, panelWin, mascotWin)` | GET /stream/{runId} → parse SSE → dispatch IPC |
| `sendMascotState(state)` | `mascotWindow.webContents.send('state-change', state)` |
| `killBackend()` | Kills `backendProcess` on app quit |

#### IPC Handler Table (ipcMain)

| Channel | Handler |
|---------|---------|
| `set-ignore-mouse-events` | `win.setIgnoreMouseEvents(ignore, opts)` |
| `drag-window` | `win.setPosition(x + deltaX, y + deltaY)` |
| `drag-end` | no-op (drag tracking cleanup) |
| `toggle-panel` | show/hide panelWindow |
| `toggle-maximize` | `panelWindow.isMaximized() ? restore : maximize` |
| `upload-pdf` | copy file → `runPipelineOrchestrator()` |
| `open-file-selector` | `dialog.showOpenDialog()` → copy → send `file-staged` |
| `trigger-upload` | `runPipelineOrchestrator()` on pre-staged file |
| `set-mascot-state` | `sendMascotState(state)` |
| `set-mascot-skin` | save to `electron-store` → forward to mascot window |
| `get-mascot-skin` | handle.invoke → returns `store.get('mascot_skin', 'mr_nerdy')` |
| `user-activity` | reset idle timer |

---

### `src/preload.js` — Context Bridge

Exposes `window.mascotAPI` to renderer processes (both panel and mascot windows) via `contextBridge.exposeInMainWorld`. All IPC calls go through this bridge — no direct `require('electron')` in renderers.

**Send methods** (R→M): `setIgnoreMouseEvents`, `dragWindow`, `dragEnd`, `togglePanel`, `toggleMaximize`, `uploadPDF`, `openFileSelector`, `triggerUpload`, `setMascotState`, `setMascotSkin`, `reportUserActivity`

**Invoke methods** (R→M awaitable): `getMascotSkin`

**Event listeners** (M→R callbacks): `onUploadStatus`, `onFileStaged`, `onPipelineLog`, `onPipelineCompleted`, `onStateChange`, `onMaximizeChange`, `onMascotSkinChange`, `onUserActivity`

---

### `src/mascot.html` — Mascot Window Shell

Minimal HTML shell for the mascot overlay window. Loads `mascot.js` and `mascot.css`. Contains a single `<canvas id="mascot-canvas">` element.

---

### `src/mascot.js` — Sprite Animation Engine

Canvas 2D sprite renderer + finite state machine for the mascot overlay.

#### Character System

```
assets/
├── mr_nerdy/   ← Classic academic nerd (Blue theme)
├── ms_nerdy/   ← Female academic variant (Teal theme)
├── mr_nerd/    ← Compact nerd (Purple theme)
└── ms_nerd/    ← Compact female variant (Coral theme)
```

Each character folder contains PNG sprite sheets for all 13 states.

#### State Machine

| State | Frames | Typical Trigger |
|-------|--------|----------------|
| `standing` | 1 | Default idle |
| `blink` | 3 | Random idle micro-animation (~30 s interval) |
| `wave` | 3 | App startup |
| `thinking` | 3 | ReACT tool execution |
| `hunch` | 3 | Chat generating (stream active) |
| `catching` | 3 | File staged in mascot drop zone |
| `excite` | 3 | Pipeline / analysis completed |
| `tired` | 3 | Extended activity (>15 min without break) |
| `having_sipping` | 3 | Long operation (>60 s stream) |
| `sleep` | 3 | Idle timeout (~3 min) |
| `angry` | 3 | Pipeline or upload error |
| `confused` | 3 | Unexpected LLM response |
| `peeking` | 3 | Transition from edge back to center |

#### Key Functions

| Function | Description |
|----------|-------------|
| `loadSprite(state)` | Loads sprite sheet PNG for current character + state |
| `playAnimation(state)` | Clears interval → loads sprite → starts frame loop |
| `setSkin(skinId)` | Switches `currentSkin` → reloads current animation with new character |
| `handleMouseEnter()` | `setIgnoreMouseEvents(false)` — captures mouse |
| `handleMouseLeave()` | `setIgnoreMouseEvents(true, {forward:true})` — restores pass-through |
| `handleClick()` | If no drag movement → `togglePanel()` |
| `handleDrag(dx, dy)` | `dragWindow({deltaX: dx, deltaY: dy})` |

---

### `src/mascot.css` — Mascot Window Styles

Minimal styles for the mascot overlay:
- `body` / `html` → transparent background, `overflow: hidden`
- `#mascot-canvas` → `cursor: pointer` on hover
- No scrollbars, no default margins

---

### `mascot_transitions.json` — State Transition Table

JSON map defining valid state-to-state transitions, used by `mascot.js` to validate state change requests and determine intermediate transition states.

---

## 📁 React Renderer (`frontend/renderer/src/`)

---

### `main.tsx` — React Entry Point

Mounts `<App />` into `#root` with `StrictMode`. No router — single-page panel application.

---

### `App.tsx` — Root Component

Renders `<Panel />` inside a full-viewport flex container with CSS variable theming.

---

### `App.css` — Base App Styles

Imports fonts and sets root-level layout constraints.

---

### `index.css` — Design System

Full CSS custom property system:

| Variable Group | Token Names |
|---------------|-------------|
| Backgrounds | `--bg-base`, `--bg-panel`, `--bg-card`, `--bg-hover`, `--bg-input` |
| Text | `--text-main`, `--text-muted`, `--text-dim` |
| Borders | `--border`, `--border-focus` |
| Accent | `--accent`, `--accent-muted` |
| Status | `--success`, `--error`, `--warning` |

**Theme variants** applied via body classes:
- `.theme-light` — Default light (l1)
- `.palette-arctic.theme-light` — Arctic blue-gray (l2)
- `.palette-iris.theme-light` — Iris purple (l3)
- No class — Dark mode (d)

---

## 📁 Store Layer (`src/store/`)

### `panelStore.ts` — Root Zustand Store

Composes 6 slices into a single `usePanelStore` hook:

```typescript
PanelState = UISlice & ProfileSlice & ChatSlice & HardwareSlice & DocumentHistorySlice & AnalysisSlice
```

Also exports the `HistoryItem` and `ChatMessage` TypeScript interfaces used across slices.

---

### `slices/uiSlice.ts`

| State | Type | Default |
|-------|------|---------|
| `isPanelOpen` | `boolean` | `true` |
| `activeView` | `'chat' \| 'profile' \| 'pdf-viewer'` | `'chat'` |
| `selectedTier` | `'brief' \| 'detailed' \| 'implement'` | `'detailed'` |
| `selectedModel` | `string` | from `localStorage['selected_model']` → `DEFAULT_SELECTED_MODEL` |
| `isLogsOpen` | `boolean` | `false` |
| `isHistoryOpen` | `boolean` | `false` |

**`setSelectedModel(model)`** — Persists to `localStorage['selected_model']`.

---

### `slices/chatSlice.ts`

| State | Type | Description |
|-------|------|-------------|
| `messages` | `ChatMessage[]` | Current conversation messages |
| `conversations` | `Conversation[]` | All threads |
| `activeConversationId` | `string \| null` | Active thread |
| `activeConversationTitle` | `string \| null` | Active thread title |
| `activePaperId` | `string \| null` | Paper scoped to current chat |
| `activePaperPath` | `string \| null` | Local path for PDF viewer |
| `isChatGenerating` | `boolean` | True while SSE stream open |
| `streamingStatus` | `string \| null` | Live backend status text |
| `streamingThought` | `string \| null` | Live ReACT thought |
| `streamingAction` | `string \| null` | Live tool name |

**Key actions:**
- `sendMessage(conversationId, message, paperId, model)` — SSE stream → parses all 7 event types → on `done`: resolves failover model, dispatches `refresh-model-limits`, updates title
- `createConversation(title, paperId)` → `POST /conversations`
- `fetchMessages(convId)` → `GET /conversations/{id}/messages`
- `fetchConversations()` → `GET /conversations`
- `selectConversation(convId)` → aborts current stream + loads messages
- `deleteConversation(convId)` → `DELETE /conversations/{id}`
- `updateConversationTitle(convId, title)` → `PATCH /conversations/{id}`
- `regenerateMessage()` — Re-sends last user message

---

### `slices/analysisSlice.ts`

| State | Type | Description |
|-------|------|-------------|
| `milestoneStatuses` | `('pending'\|'active'\|'completed')[]` | 5-slot pipeline status |
| `activeMilestoneIndex` | `number` | Currently active node index |
| `analysisStatus` | `'idle'\|'analyzing'\|'paused_for_review'\|'success'\|'error'` | Pipeline job phase |
| `uploadedFileName` | `string \| null` | Name of currently uploaded file |
| `uploadedFileType` | `'pdf' \| 'docx' \| null` | File type |
| `isAnalyzing` | `boolean` | Alias for `analysisStatus === 'analyzing'` |
| `reportContent` | `string \| null` | Final markdown report |
| `decompScore` | `number` | Decomposition quality score |
| `paramCertainty` | `number` | Hyperparameter certainty score |

**Key actions:**
- `uploadPaper(file)` → `POST /upload` via FormData → calls `startAnalysis()`
- `startAnalysis(filename, type, filePath)` → resets state + sets milestone 0 active
- `completeAnalysis(report)` → all milestones complete + stores report
- `failAnalysis(error)` → sets `analysisStatus = 'error'`
- `approveParameters(params)` → `POST /pipeline/approve`
- `generateCode(customParams)` → `POST /pipeline/ingest`
- `initIpcListeners()` → wires `window.mascotAPI` callbacks into store actions

---

### `slices/profileSlice.ts`

All fields initialise from `localStorage` and sync back on `updateProfile()`.

| State | Key in localStorage |
|-------|-------------------|
| `userId` | `local_user_id` |
| `username` | `local_username` |
| `email` | `local_email` |
| `ollamaLink` | `local_ollama_link` |
| `avatarId` | `local_avatar_id` |
| `groqApiKey` | `local_groq_api_key` |
| `openrouterApiKey` | `local_openrouter_api_key` |

`setAvatarId(id)` — simultaneously updates store, localStorage, and calls `window.mascotAPI.setMascotSkin(id)`.

---

### `slices/hardwareSlice.ts`

- `hardwareMetrics: HardwareMetrics | null` — CPU + GPU telemetry snapshot
- `isHardwareLoading: boolean`
- `fetchHardwareMetrics()` — `GET /hardware/metrics`

`HardwareMetrics` shape:
```typescript
{
  cpu: { platform, architecture, processor, cores, usage_percent, ram_total_gb, ram_used_gb, ram_available_gb },
  gpu: { cuda_available, name, vram_total_gb, vram_used_gb, vram_free_gb }
}
```

---

### `slices/documentHistorySlice.ts`

- `documentHistory: HistoryItem[]` — All uploaded papers
- `fetchDocumentHistory()` → `GET /history`
- `deleteDocument(paperId)` → `DELETE /history/{id}`

---

### `themeStore.ts` — Standalone Theme Store

Separate Zustand store (not in `panelStore`) to keep theme logic isolated.

| Mode | Body Classes | Description |
|------|-------------|-------------|
| `l1` | `.theme-light` | Default warm light |
| `l2` | `.palette-arctic .theme-light` | Arctic blue-gray light |
| `l3` | `.palette-iris .theme-light` | Iris purple light |
| `d` | (none) | Dark mode |

`toggleDarkLight()` — switches between dark and last-used light variant.

---

### `logsStore.ts` — Log Entry Store

Separate singleton Zustand store for the `LogsDrawer` panel.

- `logs: LogEntry[]` — append-only log ring buffer
- `addLog(level, message, source)` — called from `analysisSlice` on pipeline events
- `clearLogs()` — reset
- `LogEntry` → `{id, timestamp, level: 'info'|'success'|'error'|'warning', message, source}`

---

## 📁 Config & Constants (`src/config/` and `src/constants/`)

### `config/api.ts`

```typescript
export function getApiBase(): string
// → 'http://localhost:8000/api/v1' (always, in both Electron and Vite)

export const API_BASE = getApiBase();

export const API_ENDPOINTS = {
  MODELS, LIMITS, DUAL_ENGINE, PAPERS, PIPELINE_INGEST,
  CONVERSATIONS, HARDWARE, USER_PROFILE, TELEMETRY
}
```

### `constants/models.ts`

| Export | Description |
|--------|-------------|
| `FALLBACK_GROQ` | Static model list for Groq (Qwen 3.8 27B, GPT-OSS 120B) |
| `FALLBACK_OPENROUTER` | Static list (Gemini 2.5 Flash, DeepSeek R1) |
| `DEFAULT_SELECTED_MODEL` | `'qwen/qwen3.8-27b'` |
| `isExcludedModel(id)` | Returns true for embedding models or backend-reserved models |
| `resolveFailoverModelId(backendModel)` | Maps backend model string → frontend model ID for UI sync |

### `constants/branding.ts`

`APP_BRANDING` — app name, version, tagline used in `Panel.tsx` and window title.

---

## 📁 Schemas (`src/schemas/`)

### `schemas/api.ts`

Zod parse functions for all backend responses:

| Function | Validates |
|----------|-----------|
| `parseUploadResponse(data)` | `{paper_id, conversation_id, title, duplicate, limits}` |
| `parseJobStart(data)` | `{run_id, status}` |
| `parseExtractionStatus(data)` | `{status, progress, current_node}` |
| `parsePaperReport(data)` | `{report_content, paper_id, generated_at}` |
| `parseSseError(data)` | `{error, detail}` |
| `parseConversationDetail(data)` | `{id, title, paper_id, created_at}` |
| `parseChatStreamDone(data)` | `{title, model_used, failover_model, thought, action}` |

---

## 📁 Services (`src/services/`)

### `services/connectivity.ts`

Typed fetch wrappers for all backend endpoints. All functions return `Promise<T | null>` — null on any error, no thrown exceptions in UI layer.

| Function | Endpoint |
|----------|---------|
| `fetchModels()` | `GET /models` |
| `fetchModelLimits()` | `GET /models/limits` |
| `fetchDualEngineStatus()` | `GET /models/dual-engine` |
| `uploadPaperFile(file)` | `POST /upload` |
| `fetchPaperHistory()` | `GET /history` |
| `fetchConversations()` | `GET /conversations` |
| `createConversation(title, paperId)` | `POST /conversations` |
| `fetchMessages(convId)` | `GET /conversations/{id}/messages` |
| `deleteConversation(convId)` | `DELETE /conversations/{id}` |
| `fetchUserProfile(userId)` | `GET /profile` |
| `updateUserProfile(data)` | `PATCH /profile` |

---

# SECTION 2: Flow-Based Interaction Breakdown

---

## Flow A — App Startup

```
Electron launches main.js
    │
    ├─ checkBackendReady() — polls :8000 every 500ms
    │    ├─ If not running: spawn('python main.py')
    │    └─ Wait up to 60s
    │
    ├─ createPanelWindow() — loads renderer/dist/index.html
    │
    ├─ createMascotWindow() — loads src/mascot.html
    │    └─ mascot.js: reads electron-store → setSkin() → playAnimation('wave')
    │
    ├─ getTaskbarPosition() [koffi Win32 FFI]
    │    └─ positionMascotDefault(nearestDisplay)
    │
    └─ Panel: React mounts → initIpcListeners() → fetchConversations() → fetchProfile()
```

---

## Flow B — PDF Upload via Mascot (Immediate)

```
User drops PDF on mascot window
    │
    ├─ mascot.js: detectDrop() → mascotAPI.uploadPDF(path, 'pdf', model)
    │    └─ IPC: 'upload-pdf'
    │
    ├─ main.js: copyFile(src, storage/papers/) → sendMascotState('reading')
    │
    └─ runPipelineOrchestrator(filename, destPath, type, model)
           │
           ├─ POST /upload → {paper_id, run_id, conversation_id}
           │
           ├─ listenToStream(run_id)
           │    ├─ SSE: mascot-state events → sendMascotState(state)
           │    ├─ SSE: log events → panelWindow.webContents.send('pipeline-log', text)
           │    └─ SSE: done → sendMascotState('excite') [3.5s] → 'standing'
           │
           └─ panelWindow.webContents.send('pipeline-completed', {success, filename, reportContent})
```

---

## Flow C — PDF Upload via Chat Input (Staged)

```
User clicks attach in ChatInputArea
    │
    ├─ mascotAPI.openFileSelector('pdf', model)
    │    └─ IPC: 'open-file-selector'
    │    └─ main.js: dialog.showOpenDialog() → copy → send 'file-staged'
    │
    ├─ analysisSlice.initIpcListeners.onFileStaged() → setStagedFile({filename, filePath, type})
    │    └─ Panel.tsx: shows PdfAttachmentCard in ChatInputArea
    │
    └─ User sends message with staged file
           │
           ├─ mascotAPI.triggerUpload(name, path, type, model) [IPC: 'trigger-upload']
           │    └─ runPipelineOrchestrator() — same as Flow B
           │
           └─ chatSlice.sendMessage(convId, message + attachment info, paperId, model)
```

---

## Flow D — Streaming Chat Request

```
User sends message in ChatInputArea
    │
    ├─ chatSlice.sendMessage(convId, text, paperId, model)
    │
    ├─ fetch POST /conversations/{id}/chat/stream with AbortController
    │
    └─ ReadableStream reader → createSseParser()
           │
           ├─ event: status  → set streamingStatus
           ├─ event: thought → set streamingThought
           ├─ event: action  → set streamingAction
           ├─ event: token   → append to message content (streaming text)
           └─ event: done    → {
                  finalizeMessage(),
                  resolveFailoverModelId(failover_model) → setSelectedModel(),
                  dispatchEvent('refresh-model-limits'),
                  set isChatGenerating = false
              }
```

---

## Flow E — Mascot Skin Switch

```
User selects skin in MascotSelector.tsx
    │
    ├─ profileSlice.setAvatarId(skinId)
    │    ├─ localStorage.setItem('local_avatar_id', skinId)
    │    └─ window.mascotAPI.setMascotSkin(skinId)  [IPC: 'set-mascot-skin']
    │
    ├─ main.js: electron-store.set('mascot_skin', skinId)
    │    └─ mascotWindow.webContents.send('mascot-skin-change', skinId)
    │
    └─ mascot.js: onMascotSkinChange(skinId)
           └─ setSkin(skinId) → reload sprites → playAnimation(currentState)
```

---

## Flow F — Theme Change

```
User clicks ThemeToggle.tsx
    │
    ├─ themeStore.toggleDarkLight()
    │    ├─ if dark → setThemeMode(lastLightVariant)
    │    └─ if light → setThemeMode('d')
    │
    └─ applyThemeToDocument(mode)
           ├─ remove: 'theme-light', 'palette-arctic', 'palette-iris'
           └─ add appropriate class(es) → CSS variables update instantly
```

---

# SECTION 3: Input/Output Specifications

---

## `chatSlice.sendMessage(conversationId, message, paperId?, modelName?)`

- **Input:** Conv ID string, message text string, optional paper ID, optional model ID
- **Output:** `AsyncGenerator` via SSE — progressively updates Zustand `messages[]` in-place
- **Side effects:** updates `isChatGenerating`, `streamingStatus`, `streamingThought`, `streamingAction`, dispatches `refresh-model-limits` on completion

---

## `analysisSlice.uploadPaper(file: File)`

- **Input:** Browser `File` object (PDF or DOCX)
- **Output:** `Promise<void>` — stores `{paper_id, conversation_id}` and calls `startAnalysis()`
- **Errors:** sets `analysisStatus = 'error'` on `!response.ok`

---

## `ModelSelector.tsx` props

```typescript
interface ModelSelectorProps {
  selectedModel: string;         // from uiSlice.selectedModel
  onModelChange: (id: string) => void; // calls setSelectedModel + stores to localStorage
  groups: ProviderGroup[];       // from GET /models response
  disabled?: boolean;            // true while isChatGenerating
}
```

---

## `MilestoneTracker.tsx` props

```typescript
interface MilestoneTrackerProps {
  milestoneStatuses: ('pending' | 'active' | 'completed')[];  // 5-element array
  activeMilestoneIndex: number;
  analysisStatus: string;
}
```

---

## `ReActStepsAccordion.tsx` props

```typescript
interface ReActStepsAccordionProps {
  thought: string | null;      // THOUGHT block text
  action: string | null;       // ACTION / tool name
  observation: string | null;  // OBSERVATION text
  isExpanded?: boolean;        // default collapsed
}
```

---

## `ProviderQuotaCard.tsx` props

```typescript
interface ProviderQuotaCardProps {
  provider: string;           // 'groq' | 'openrouter' | 'local'
  rpm_used: number;
  rpm_limit: number;
  rpd_used: number;
  rpd_limit: number;
  available: boolean;         // false if provider key missing
}
```

---

## `window.mascotAPI` TypeScript Declaration

```typescript
declare global {
  interface Window {
    mascotAPI?: {
      // Send (R→M)
      setIgnoreMouseEvents: (ignore: boolean, options?: {forward: boolean}) => void;
      dragWindow: (delta: {deltaX: number; deltaY: number}) => void;
      dragEnd: () => void;
      togglePanel: () => void;
      toggleMaximize: () => void;
      uploadPDF: (filePath: string, type: string, modelName: string) => void;
      openFileSelector: (type: string, modelName: string) => void;
      triggerUpload: (filename: string, filePath: string, type: string, modelName: string) => void;
      setMascotState: (state: string) => void;
      setMascotSkin: (skinId: string) => void;
      reportUserActivity: () => void;
      // Invoke (R→M, async)
      getMascotSkin: () => Promise<string>;
      // Listen (M→R)
      onUploadStatus: (cb: (result: {success: boolean; filename: string}) => void) => void;
      onFileStaged: (cb: (result: {success: boolean; filename: string; filePath: string; type: string; modelName: string}) => void) => void;
      onPipelineLog: (cb: (data: {text: string}) => void) => void;
      onPipelineCompleted: (cb: (result: {success: boolean; filename: string; reportContent?: string; error?: string}) => void) => void;
      onStateChange: (cb: (state: string) => void) => void;
      onMaximizeChange: (cb: (isMaximized: boolean) => void) => void;
      onMascotSkinChange: (cb: (skinId: string) => void) => void;
      onUserActivity: (cb: () => void) => void;
    };
  }
}
```

---

## Key Dependencies

### Electron App (`electron_app/package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `electron` | 43 | Desktop runtime |
| `electron-store` | 11 | Persistent key-value (mascot skin) |
| `koffi` | 3 | Win32 FFI (taskbar position) |
| `active-win` | 8 | Active window title polling |
| `electron-builder` | latest | Production packaging |

### React Renderer (`renderer/package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 19 | UI framework |
| `vite` | 8 | Build tool + dev server |
| `zustand` | 5 | State management (slice pattern) |
| `zod` | 4 | Runtime response validation |
| `motion` | 13 | Animation library |
| `lucide-react` | latest | SVG icon set |
| `@rive-app/react-canvas` | latest | Rive animation runtime |
| `@fontsource/ibm-plex-mono` | latest | Code font |
| `@fontsource/public-sans` | latest | UI font |
| `@fontsource/source-serif-4` | latest | Reading/report font |
| `typescript` | 6 | Type safety |
| `tailwindcss` | 4 | Utility CSS (dev only) |
