# 🎨 Frontend Architecture — Phase-wise Technical Explanation

> **System:** RUEXIS AI Platform v2.0 Desktop App  
> **Tech Stack:** Electron 43 · React 19 · TypeScript 6 · Vite 8 · Zustand 5 · TailwindCSS 4 · Motion  
> **Native Bindings:** `koffi` (Win32 taskbar FFI) · `active-win` (window polling) · `electron-store` (persistence)  
> **Structure:** Two-app system — `electron_app/` (desktop container) + `renderer/` (React UI)

---

## Phase 1 — Electron Desktop Shell & Mascot Overlay (Days 15–17)

### Day 15: Main Process — Window Architecture

**What it does:** Establishes the two-window Electron application — a main panel and a transparent mascot overlay.

**Key elements:**

- **Panel Window** (`createPanelWindow()`) — 1100×900 `BrowserWindow` loading `renderer/dist/index.html` (production) or `http://localhost:5173` (dev)
- **Mascot Window** (`createMascotWindow()`) — 125×150 frameless, transparent, always-on-top overlay loading `src/mascot.html`
- **Backend Auto-Spawn** — `checkBackendReady()` polls `http://localhost:8000` every 500 ms; spawns `python main.py` as a child process if not already running
- **App lifecycle** — `backendProcess` is killed on `app.quit()` to prevent orphan processes

---

### Day 16: Win32 Taskbar Detection & DPI-Aware Positioning

**What it does:** Positions the mascot precisely at the bottom-right of the usable screen area, accounting for taskbar position and DPI scaling.

**Key elements:**

- **`koffi` FFI bindings** — Loads `shell32.dll` and maps `SHAppBarMessage` with `APPBARDATA` struct to call `ABM_GETTASKBARPOS` (message 5)
- **Taskbar edge detection** — Returns `{left, top, right, bottom, edge}` where edge `0=Left`, `1=Top`, `2=Right`, `3=Bottom`
- **`positionMascotDefault(nearestDisplay)`** — Sizes mascot by `scaleFactor` and places it at `workArea.x + workArea.width - mascotWidth - 24px` / `workArea.y + workArea.height - mascotHeight`
- **Multi-monitor** — `screen.on('display-metrics-changed')` re-positions mascot on resolution change, scale change, or monitor connect/disconnect
- **Graceful fallback** — If `koffi` fails to load, Electron's native `workArea` is used directly

---

### Day 17: Mascot Sprite Animation Engine & State Machine

**What it does:** Implements a Canvas 2D sprite animation engine with a 13-state finite state machine.

**Key elements:**

- **4 Character Sprites** — `mr_nerdy`, `ms_nerdy`, `mr_nerd`, `ms_nerd` (each in `assets/{character}/`)
- **13 Animation States** — `standing`, `blink`, `wave`, `thinking`, `hunch`, `catching`, `excite`, `tired`, `having_sipping`, `sleep`, `angry`, `confused`, `peeking`
- **Sprite rendering** — Each state loads a horizontal sprite sheet (N-frame × frame-width); `setInterval` advances frames
- **State triggers** — Backend SSE `mascot-state` events → `sendMascotState()` in `main.js` → `webContents.send('state-change', state)` → `mascot.js` applies new animation
- **Transition table** — `mascot_transitions.json` defines valid state → state paths
- **Idle timer** — User inactivity > ~3 min → `tired` → `sleep`

---

## Phase 2 — IPC Bridge & File Upload Flow (Days 18–19)

### Day 18: Preload Context Bridge (`preload.js`)

**What it does:** Exposes a secure `window.mascotAPI` object to both the mascot renderer and panel renderer using Electron's `contextBridge`.

**Full IPC API surface:**

| Method | Direction | Description |
|--------|-----------|-------------|
| `setIgnoreMouseEvents(ignore, opts)` | R→M | Enable/disable click-through |
| `dragWindow({deltaX, deltaY})` | R→M | Move mascot window |
| `dragEnd()` | R→M | Signal drag completion |
| `togglePanel()` | R→M | Show/hide panel window |
| `toggleMaximize()` | R→M | Maximize/restore panel |
| `uploadPDF(path, type, model)` | R→M | Copy + immediately pipeline |
| `openFileSelector(type, model)` | R→M | Native dialog → stage only |
| `triggerUpload(name, path, type, model)` | R→M | Run pipeline on staged file |
| `setMascotState(state)` | R→M | Drive mascot animation |
| `setMascotSkin(skinId)` | R→M | Switch character |
| `getMascotSkin()` | invoke | Get stored skin from electron-store |
| `reportUserActivity()` | R→M | Reset idle timer |
| `onUploadStatus(cb)` | M→R | File copy result |
| `onFileStaged(cb)` | M→R | File staged result |
| `onPipelineLog(cb)` | M→R | Live log text |
| `onPipelineCompleted(cb)` | M→R | Job done / error |
| `onStateChange(cb)` | M→R | Mascot state update |
| `onMaximizeChange(cb)` | M→R | Panel maximize state |
| `onMascotSkinChange(cb)` | M→R | Skin switched |

---

### Day 19: File Upload & Pipeline Orchestration

**What it does:** Manages the full file-to-pipeline lifecycle from the Electron main process.

**Two upload paths:**

| Path | Trigger | Behaviour |
|------|---------|-----------|
| **Immediate** | `upload-pdf` IPC | Copy → mascot `reading` → `runPipelineOrchestrator()` immediately |
| **Staged** | `open-file-selector` → `trigger-upload` | Copy → mascot `catching` → wait for user send → then `runPipelineOrchestrator()` |

**`runPipelineOrchestrator(filename, path, type, model)`:**
1. `POST /upload` → receives `{paper_id, run_id, conversation_id}`
2. `listenToStream(run_id, ...)` → SSE from `/stream/{run_id}`
3. Forwards `pipeline-log` events → panel via `webContents.send`
4. Forwards `mascot-state` events → `sendMascotState(state)`
5. On complete: mascot `excited` (3.5 s) → `idle`; panel receives `pipeline-completed`

---

## Phase 3 — React Renderer UI (Days 20–22)

### Day 20: Application Shell & Root Store

**What it does:** Establishes the React entry point, root Zustand store, and top-level panel layout.

**Key elements:**

- **`main.tsx`** — Mounts `<App />` into `#root`
- **`App.tsx`** — Renders single `<Panel />` component with full-viewport layout
- **`Panel.tsx`** — Root panel orchestrator: owns `isSidebarOpen`, `stagedFile`, `isDragging`, `chatInputValue`; calls `initIpcListeners()` on mount to wire all `window.mascotAPI.on*` callbacks
- **`panelStore.ts`** — Root Zustand store composing 6 slices: `UISlice + ProfileSlice + ChatSlice + HardwareSlice + DocumentHistorySlice + AnalysisSlice`
- **`index.css`** — Full design system: CSS variables for all theme colors, IBM Plex Mono / Public Sans / Source Serif 4 fonts, animations

---

### Day 21: Zustand State Slices

**What it does:** Each feature area has its own isolated Zustand slice.

#### `uiSlice.ts` — UI State
| State | Default | Description |
|-------|---------|-------------|
| `isPanelOpen` | `true` | Panel visibility |
| `activeView` | `'chat'` | Current view: `'chat'` / `'profile'` / `'pdf-viewer'` |
| `selectedTier` | `'detailed'` | Output depth: `'brief'` / `'detailed'` / `'implement'` |
| `selectedModel` | from `localStorage` | Active inference model ID (persisted) |
| `isLogsOpen` | `false` | Logs drawer open state |
| `isHistoryOpen` | `false` | History sidebar open state |

#### `chatSlice.ts` — Chat & Conversations
- `messages`, `conversations`, `activeConversationId`, `isChatGenerating`, `streamingStatus/Thought/Action`
- `sendMessage()` — Opens SSE to `/chat/stream`, parses all 7 event types, dispatches `refresh-model-limits` on `done`
- `createConversation()`, `fetchMessages()`, `fetchConversations()`, `selectConversation()`, `deleteConversation()`, `updateConversationTitle()`, `regenerateMessage()`

#### `analysisSlice.ts` — Pipeline & Papers
- `milestoneStatuses` (`pending`/`active`/`completed` × 5), `analysisStatus`, `reportContent`, `decompScore`, `paramCertainty`
- `uploadPaper(file)` — `POST /upload` via `FormData` → triggers backend pipeline
- `startAnalysis()`, `completeAnalysis()`, `failAnalysis()`, `approveParameters()`, `generateCode()`
- `initIpcListeners()` — Wires `onPipelineLog`, `onPipelineCompleted`, `onFileStaged`, `onUploadStatus` from `window.mascotAPI`

#### `profileSlice.ts` — User Profile & API Keys
- `username`, `email`, `ollamaLink`, `groqApiKey`, `openrouterApiKey`, `avatarId`
- Initialises from `localStorage`; persists back on every update
- `setAvatarId(id)` — Updates store + calls `window.mascotAPI.setMascotSkin(id)`
- `fetchProfile()` / `updateProfile()` — `GET|PATCH /profile`

#### `hardwareSlice.ts` — Hardware Metrics
- `fetchHardwareMetrics()` — `GET /hardware/metrics`; stores CPU + GPU telemetry

#### `documentHistorySlice.ts` — Paper History
- `fetchDocumentHistory()` — `GET /history`; populates `HistoryItem[]` list

#### `themeStore.ts` — Theme (separate singleton store)
- **4 theme modes:** `'l1'` (default light) · `'l2'` (Arctic palette) · `'l3'` (Iris palette) · `'d'` (dark)
- `applyThemeToDocument(mode)` — Adds/removes `theme-light`, `palette-arctic`, `palette-iris` CSS classes on `document.body`
- Persisted to `localStorage` under `ruexis_theme_mode`

---

### Day 22: Layout & Feature Components

**What it does:** Assembles the full UI from layout shells and feature components.

#### Layout (`src/components/layout/`)
| Component | Description |
|-----------|-------------|
| `Header.tsx` | Top bar: model selector, tier selector, theme toggle, view tabs (Chat / Profile) |
| `LeftSidebar.tsx` | Collapsible left panel: chat history list, document history list, user profile card |
| `RightSidebar.tsx` | Right panel: pipeline milestone tracker, report view, analysis progress |
| `ChatHistoryList.tsx` | Conversation CRUD list with rename, delete, select |
| `DocumentHistoryList.tsx` | Paper upload history with delete and inline PDF viewer |
| `CompactHistoryDropdown.tsx` | Compact conversation selector for narrow layouts |
| `MascotBox.tsx` | In-panel mascot iframe embed (mirrors overlay character) |
| `UserProfileCard.tsx` | Mini profile card in sidebar |

#### Chat Features (`src/components/features/chat/`)
| Component | Description |
|-----------|-------------|
| `MessageFeed.tsx` | Scrollable message list with auto-scroll |
| `MessageBubble.tsx` | User/assistant bubble with markdown code rendering |
| `ChatInputArea.tsx` | Textarea with send, file attach, model indicator, staged file card |
| `ReActStepsAccordion.tsx` | Collapsible THOUGHT / ACTION / OBSERVATION traces |
| `parseReAct.ts` | Parses raw ReACT text into structured trace objects |

#### Analysis Features (`src/components/features/analysis/`)
| Component | Description |
|-----------|-------------|
| `MilestoneTracker.tsx` | 5-step pipeline milestone progress bar |
| `ReportView.tsx` | Final analysis report renderer with markdown + code blocks |
| `ParameterConfigForm.tsx` | Hyperparameter approval/edit form before code generation |
| `DocumentsDrawer.tsx` | Uploaded paper list panel |
| `ImplementationTabs.tsx` | Code + milestones tabbed view |
| `PdfViewerPage.tsx` | Inline PDF viewer (loads from `/papers/{id}/pdf`) |
| `StatsCharts.tsx` | Pipeline timing charts |
| `ScholarBadge.tsx` | Citation/scholar source badge |

#### Profile Features (`src/components/features/profile/`)
| Component | Description |
|-----------|-------------|
| `UserProfile.tsx` | Full profile page (API keys, Ollama, mascot, limits) |
| `ApiKeysConfigSection.tsx` | Groq + OpenRouter key input/save |
| `OllamaConfigSection.tsx` | Ollama host URL configuration |
| `ModelLimitsSection.tsx` | Live quota dashboard for all providers |
| `ProviderQuotaCard.tsx` | Per-provider rate limit usage card |
| `ServerMetricsBadge.tsx` | Backend online/offline status indicator |
| `MascotSelector.tsx` | Character skin selector (4 options) |

#### UI Components (`src/components/ui/`)
| Component | Description |
|-----------|-------------|
| `ModelSelector.tsx` | Provider-grouped model dropdown; auto-ticks on failover |
| `DropZone.tsx` | Drag-and-drop PDF/DOCX upload zone |
| `DragDropOverlay.tsx` | Full-screen drag overlay animation |
| `LocalAuthModal.tsx` | First-boot login modal |
| `ThemeToggle.tsx` | Dark/light cycle button |
| `Icons.tsx` | Centralized SVG icon library |
| `Loader.tsx` / `MessageSkeleton.tsx` | Loading states |
| `SkinLoader.tsx` | Mascot skin preview preloader |
| `PdfAttachmentCard.tsx` | Staged file preview in chat input |
| `Tooltip.tsx` | Accessible hover tooltip wrapper |
| `TierSelector.tsx` | Output depth selector (Brief / Detailed / Implement) |

---

## Phase 4 — SSE Streaming & Model Failover (Days 23–24)

### Day 23: Chat SSE Stream Parser

**What it does:** Implements a robust Server-Sent Events parser in `chatSlice.ts` that handles the full event protocol.

**`createSseParser(dispatcher)` handles:**

| SSE Event | Action |
|-----------|--------|
| `status` | Updates `streamingStatus` → shown below model name in UI |
| `thought` | Updates `streamingThought` → shown in ReActStepsAccordion |
| `action` | Updates `streamingAction` → tool name display |
| `observation` | Appended to ReACT trace |
| `token` | Appended to current message content (streaming text) |
| `done` | Finalizes message, updates title, resolves failover model |
| `error` | Shows error message, sets `isChatGenerating = false` |

- **AbortController** — `currentAbortController` aborts in-flight requests on conversation switch
- **JSON-wrapped events** — Parser handles legacy `{event, data}` JSON payloads as well as standard SSE format

---

### Day 24: Model Failover Sync

**What it does:** Automatically ticks the correct model in `ModelSelector` when the backend falls over to a different provider.

**Flow:**
```
SSE done event: {failover_model: "openrouter/google/gemini-2.5-flash"}
    │
    ▼
resolveFailoverModelId("openrouter/google/gemini-2.5-flash")
    → returns "google/gemini-2.5-flash"
    │
    ▼
usePanelStore.setSelectedModel("google/gemini-2.5-flash")
+ localStorage.setItem("selected_model", ...)
    │
    ▼
ModelSelector re-renders → correct model ticked
```

After `done`, `chatSlice` dispatches `window.dispatchEvent(new CustomEvent('refresh-model-limits'))` to trigger a fresh quota fetch in `ModelLimitsSection`.

---

## Phase 5 — Theming, Config & Production Build (Days 25–28)

### Day 25: Design System (`index.css`)

**What it does:** Defines all CSS custom properties for the full design system.

- **Dark mode** — Default: `--bg-base`, `--bg-panel`, `--bg-card`, `--text-main`, `--text-muted`, `--border`, `--accent`
- **Light mode** — `.theme-light` class overrides; `.palette-arctic` and `.palette-iris` provide alternative light palettes
- **Fonts** — IBM Plex Mono (code/mono), Public Sans (UI), Source Serif 4 (reading/report)
- **Animations** — `fade-in`, `slide-up`, `shimmer` (skeleton loading), `typing-cursor`

### Day 26: Vite Configuration

**What it does:** Configures Vite for both development and Electron production builds.

- **Dev proxy** — `/api` → `http://localhost:8000` for browser-only dev
- **Build output** — `dist/` loaded by Electron in production
- **TailwindCSS v4** — Via `@tailwindcss/vite` plugin (dev-only utility classes)

### Day 27: API & Schema Layer

- **`src/config/api.ts`** — `getApiBase()` resolves to `http://localhost:8000/api/v1` in both Electron and Vite dev
- **`src/schemas/api.ts`** — Zod schemas for all backend responses: `parseUploadResponse`, `parseChatStreamDone`, `parseConversationDetail`, etc.
- **`src/constants/models.ts`** — `FALLBACK_GROQ`, `FALLBACK_OPENROUTER`, `DEFAULT_SELECTED_MODEL`, `isExcludedModel()`, `resolveFailoverModelId()`

### Day 28: Production Build Flow

```bash
# 1. Build renderer
cd frontend/renderer && npm run build
# → outputs to frontend/renderer/dist/

# 2. Launch Electron (loads dist/index.html)
cd frontend/electron_app && npm start
```

In development:
```bash
cd frontend/renderer && npm run dev     # Vite dev at :5173
cd frontend/electron_app && npm start   # Electron loads :5173
```
