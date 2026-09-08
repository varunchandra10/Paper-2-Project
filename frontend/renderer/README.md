# RUEXIS AI — Renderer (React Frontend)

The web UI layer of the RUEXIS AI desktop application. Built with React 19 + Vite + Zustand + TypeScript. Rendered inside the Electron BrowserWindow as a file:// page in production, and served by Vite dev server at `http://localhost:5173` during development.

---

## Quick Start

```bash
cd frontend/renderer

# Install dependencies
npm install

# Start development server (talks to backend at localhost:8000)
npm run dev

# Build production bundle (loaded by Electron in production)
npm run build
```

Dev server: **http://localhost:5173**

---

## Directory Structure

```
renderer/
├── index.html              # Vite HTML entry point
├── vite.config.ts          # Vite config
├── package.json            # Dependencies
└── src/
    ├── main.tsx            # React root mount
    ├── App.tsx             # Top-level router / panel layout
    ├── index.css           # Global design system (CSS variables, typography, animations)
    ├── config/
    │   └── api.ts          # Centralized API base URL + endpoint constants
    ├── constants/
    │   └── models.ts       # Model catalog fallbacks, DEFAULT_SELECTED_MODEL, resolveFailoverModelId
    ├── schemas/
    │   └── api.ts          # Zod schemas for all backend response types
    ├── services/
    │   └── connectivity.ts # Fetch wrappers for all backend endpoints
    ├── store/
    │   ├── panelStore.ts   # Root Zustand store (panel state, chat messages)
    │   ├── logsStore.ts    # Log entry store for the Logs panel
    │   ├── themeStore.ts   # Theme (dark/light) persistence via localStorage
    │   ├── utils/          # Shared store utilities (API_BASE, etc.)
    │   └── slices/
    │       ├── chatSlice.ts          # Chat state, SSE streaming, conversation CRUD
    │       ├── analysisSlice.ts      # Pipeline/analysis state, paper upload, report
    │       ├── profileSlice.ts       # User profile, API keys, Ollama config
    │       ├── documentHistorySlice.ts # Document history list state
    │       ├── hardwareSlice.ts      # Hardware metrics polling state
    │       └── uiSlice.ts            # UI state: selectedModel, selectedMascot
    ├── components/
    │   ├── layout/
    │   │   ├── Header.tsx            # Top bar with model selector, theme toggle, tabs
    │   │   ├── LeftSidebar.tsx       # Conversation history + document history panel
    │   │   ├── RightSidebar.tsx      # Analysis pipeline progress, report view
    │   │   ├── ChatHistoryList.tsx   # Conversation thread list with CRUD
    │   │   ├── DocumentHistoryList.tsx # Paper history list with upload/delete
    │   │   ├── CompactHistoryDropdown.tsx # Compact conversation selector
    │   │   ├── MascotBox.tsx         # In-panel mascot iframe embed
    │   │   └── UserProfileCard.tsx   # Profile card in sidebar
    │   ├── features/
    │   │   ├── chat/
    │   │   │   ├── ChatInputArea.tsx       # Message input, file attachment, send
    │   │   │   ├── MessageBubble.tsx       # User/assistant message bubble renderer
    │   │   │   ├── MessageFeed.tsx         # Scrollable message list
    │   │   │   ├── ReActStepsAccordion.tsx # Collapsible ReACT thought/action/observation trace
    │   │   │   ├── parseReAct.ts           # ReACT trace parser
    │   │   │   └── messageFormatters.tsx   # Markdown/code formatting helpers
    │   │   ├── analysis/
    │   │   │   ├── DocumentsDrawer.tsx     # Uploaded paper list panel
    │   │   │   ├── ParameterConfigForm.tsx # Hyperparameter approval/edit form
    │   │   │   ├── MilestoneTracker.tsx    # Implementation milestone progress
    │   │   │   ├── ReportView.tsx          # Final analysis report renderer
    │   │   │   ├── ImplementationTabs.tsx  # Code + milestones tabs
    │   │   │   ├── PdfViewerPage.tsx       # Inline PDF viewer
    │   │   │   ├── StatsCharts.tsx         # Pipeline stats charts
    │   │   │   └── ScholarBadge.tsx        # Citation badge
    │   │   ├── profile/
    │   │   │   ├── UserProfile.tsx         # Full user profile page (keys, Ollama, mascot)
    │   │   │   ├── ApiKeysConfigSection.tsx  # API key input/save section
    │   │   │   ├── OllamaConfigSection.tsx   # Ollama host link configuration
    │   │   │   ├── ModelLimitsSection.tsx    # Quota dashboard with live rate limit metrics
    │   │   │   ├── ProviderQuotaCard.tsx     # Per-provider quota usage card
    │   │   │   ├── ServerMetricsBadge.tsx    # Backend server status badge
    │   │   │   └── MascotSelector.tsx        # Mascot character selection
    │   │   └── logs/
    │   │       └── (log panel components)
    │   ├── ui/
    │   │   ├── ModelSelector.tsx       # Model dropdown with provider groups, failover tick
    │   │   ├── DropZone.tsx            # Drag-and-drop PDF upload zone
    │   │   ├── DragDropOverlay.tsx     # Full-screen drag overlay
    │   │   ├── LocalAuthModal.tsx      # Local auth login modal
    │   │   ├── ThemeToggle.tsx         # Dark/light theme toggle button
    │   │   ├── Icons.tsx               # Centralized SVG icon library
    │   │   ├── Loader.tsx              # Spinner/loading components
    │   │   ├── MessageSkeleton.tsx     # Skeleton loader for messages
    │   │   ├── SkinLoader.tsx          # Mascot skin preview loader
    │   │   ├── PdfAttachmentCard.tsx   # Attached PDF preview card
    │   │   ├── TierSelector.tsx        # Provider tier filter
    │   │   └── Tooltip.tsx             # Accessible tooltip wrapper
    │   └── mascot/
    │       └── (mascot state components)
    ├── assets/                         # Static images and mascot sprite sheets
    └── utils/                          # Shared utility functions
```

---

## State Management — Zustand Slices

The root store is `panelStore.ts`. Each feature area is a separate slice composed into the root store.

### `uiSlice.ts` — UI State

| State | Type | Description |
|-------|------|-------------|
| `selectedModel` | `string` | Currently selected inference model ID. Persisted to `localStorage`. |
| `selectedMascot` | `string` | Currently selected mascot character ID. Persisted to `localStorage`. |

**Auto-Failover Sync:** When the backend returns a `failover_model` field in the SSE `done` event, `chatSlice` calls `resolveFailoverModelId()` and updates `selectedModel` automatically so the correct model is ticked in the selector.

---

### `chatSlice.ts` — Chat & Conversation State

| State | Type | Description |
|-------|------|-------------|
| `messages` | `ChatMessage[]` | Current conversation messages |
| `conversations` | `Conversation[]` | All conversation threads |
| `activeConversationId` | `string \| null` | Currently active conversation |
| `isChatGenerating` | `boolean` | True while SSE stream is active |
| `streamingStatus` | `string \| null` | Live ReACT status text |
| `streamingThought` | `string \| null` | Live ReACT thought trace |
| `streamingAction` | `string \| null` | Live ReACT action trace |

**Key Actions:**
- `sendMessage()` — Opens SSE stream to `POST /conversations/{id}/chat/stream`, handles all events (`token`, `done`, `error`, `status`, `thought`, `action`). On `done`, dispatches `refresh-model-limits` window event to update quota cards.
- `createConversation()` — `POST /conversations`
- `fetchMessages()` — `GET /conversations/{id}/messages`
- `fetchConversations()` — `GET /conversations`
- `selectConversation()` — Switches active conversation + aborts any in-flight request
- `deleteConversation()` — `DELETE /conversations/{id}`
- `updateConversationTitle()` — `PATCH /conversations/{id}`
- `regenerateMessage()` — Re-sends the last user message

---

### `analysisSlice.ts` — Pipeline & Paper State

Manages the full paper upload → analysis → report lifecycle.

| State | Type | Description |
|-------|------|-------------|
| `papers` | `Paper[]` | All uploaded paper records |
| `activePaperId` | `string \| null` | Currently selected paper |
| `analysisStatus` | `string` | Current pipeline job status |
| `pipelineLogs` | `string[]` | Live SSE pipeline log lines |
| `reportContent` | `string \| null` | Final generated analysis report |
| `hyperparameters` | `object \| null` | Extracted ML hyperparameters |

**Key Actions:**
- `uploadPaper()` — `POST /upload` → triggers pipeline
- `fetchPaperHistory()` — `GET /history`
- `fetchReport()` — `GET /pipeline/report/{paper_id}`
- `approvePipelineStep()` — `POST /pipeline/approve`
- `fetchHyperparameters()` — `GET /history/{paper_id}/hyperparameters`

---

### `profileSlice.ts` — User Profile & Config

| State | Type | Description |
|-------|------|-------------|
| `userProfile` | `Profile \| null` | User metadata and configured API keys |
| `hardwareMetrics` | `HardwareMetrics \| null` | Live CPU/GPU telemetry |
| `modelLimits` | `ModelLimits \| null` | Provider quota data |

**Key Actions:**
- `fetchProfile()` — `GET /profile`
- `updateProfile()` — `PATCH /profile` (saves API keys, Ollama link)
- `fetchHardwareMetrics()` — `GET /hardware/metrics`
- `fetchModelLimits()` — `GET /models/limits`

---

## API Configuration

`src/config/api.ts` provides a single source of truth for all backend endpoint URLs:

```typescript
export const API_BASE = 'http://localhost:8000/api/v1';  // auto-resolved

export const API_ENDPOINTS = {
  MODELS: `${API_BASE}/models`,
  LIMITS: `${API_BASE}/models/limits`,
  DUAL_ENGINE: `${API_BASE}/models/dual-engine`,
  PAPERS: `${API_BASE}/papers`,
  PIPELINE_INGEST: `${API_BASE}/pipeline/ingest`,
  CONVERSATIONS: `${API_BASE}/conversations`,
  HARDWARE: `${API_BASE}/hardware/metrics`,
  USER_PROFILE: `${API_BASE}/user/profile`,
  TELEMETRY: `${API_BASE}/telemetry/traces`,
};
```

In Electron production (file:// protocol), `getApiBase()` always resolves to `http://localhost:8000/api/v1`. In browser development with Vite, it uses `VITE_BACKEND_URL` if set, otherwise defaults to the same.

---

## Model Selector & Auto-Failover

`src/constants/models.ts` defines:

| Export | Description |
|--------|-------------|
| `FALLBACK_GROQ` | Static fallback model list for Groq (Qwen 3.8 27B, GPT-OSS 120B) |
| `FALLBACK_OPENROUTER` | Static fallback for OpenRouter (Gemini 2.5 Flash, DeepSeek R1) |
| `DEFAULT_SELECTED_MODEL` | `'qwen/qwen3.8-27b'` — default on first launch |
| `isExcludedModel()` | Filters out embedding models and backend-reserved models |
| `resolveFailoverModelId()` | Maps a backend `model_used` string to a frontend model ID when automatic failover occurred |

`ModelSelector.tsx` renders provider groups (Groq / OpenRouter / Local Ollama) fetched live from `GET /models`. The active option is driven by `selectedModel` from `uiSlice`.

When the backend fails over to a different provider mid-request:
1. The SSE `done` event includes `failover_model` in the JSON payload
2. `chatSlice.sendMessage()` calls `resolveFailoverModelId(failover_model)`
3. If a frontend model ID is resolved, `uiSlice.setSelectedModel()` is called
4. `ModelSelector` immediately re-renders with the correct model ticked

---

## Quota Dashboard

`ModelLimitsSection.tsx` + `ProviderQuotaCard.tsx` render a live rate-limit dashboard populated by `GET /models/limits`.

- After every chat completion, `chatSlice` dispatches `window.dispatchEvent(new CustomEvent('refresh-model-limits'))` to trigger a fresh quota fetch.
- `ProviderQuotaCard` calculates accurate usage percentages from raw `used` / `limit` fields — no hardcoded values.
- Displays separate cards per provider: **Groq**, **OpenRouter**, and **Local Ollama** (when configured).

---

## SSE Stream Parsing

`chatSlice.ts` includes a custom SSE parser (`createSseParser`) that:
- Handles standard `event: / data:` multi-line SSE format
- Detects and unwraps JSON-wrapped events (legacy backend compatibility)
- Dispatches to typed handlers: `onToken`, `onDone`, `onError`, `onStatus`, `onThought`, `onAction`
- Supports graceful abort via `AbortController` on conversation switch

---

## Design System

`src/index.css` defines the full design system:

- **Typography:** IBM Plex Mono (code), Public Sans (UI), Source Serif 4 (reading)
- **Color Tokens:** CSS custom properties for all theme colors in dark and light modes
- **Animations:** Fade-in, slide-up, shimmer skeleton, typing cursor
- **Theme Toggle:** Persisted via `themeStore.ts` to `localStorage`

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `react` 19 | UI framework |
| `vite` 8 | Build tool + dev server |
| `zustand` 5 | State management (slice pattern) |
| `zod` 4 | Runtime response schema validation |
| `motion` 13 | Animation library |
| `lucide-react` | SVG icon set |
| `@rive-app/react-canvas` | Rive animation runtime (mascot) |
| `@fontsource/*` | Self-hosted fonts (IBM Plex Mono, Public Sans, Source Serif 4) |
| `typescript` 6 | Type safety |
| `tailwindcss` 4 | Utility CSS (dev only, used sparingly) |
