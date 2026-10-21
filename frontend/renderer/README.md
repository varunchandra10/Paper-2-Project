# RUEXIS AI — Renderer (React Frontend)

The core web UI application of RUEXIS AI. Built with React 19, TypeScript, Vite, Zustand 5, and TailwindCSS v4. It runs embedded inside the Electron desktop container and can be hosted standalone during browser development.

---

## ⚡ Quick Start

```bash
cd frontend/renderer

# Install dependencies
npm install

# Start Vite development server
npm run dev

# Run TypeScript type check
npm run typecheck

# Build production bundle (compiled into dist/)
npm run build

# Preview production build locally
npm run preview
```

- **Dev Server URL:** `http://localhost:5173`
- **Preview Server URL:** `http://localhost:4173`
- **Backend Target:** `http://localhost:8000/api/v1`

---

## 🛠️ Available Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| `npm run dev` | `vite` | Starts local hot-reloading development server on port 5173 |
| `npm run build` | `tsc -b && vite build` | Type-checks project and bundles static assets into `dist/` |
| `npm run typecheck` | `tsc --noEmit` | Fast TypeScript validation without writing output files |
| `npm run lint` | `eslint .` | Runs ESLint over all TS, TSX, and JS files |
| `npm run preview` | `vite preview` | Serves the production `dist/` bundle on port 4173 |

---

## 📁 Directory Structure

```
renderer/
├── index.html              # Single Page Application HTML shell
├── vite.config.ts          # Vite configuration with React & Tailwind v4 plugins
├── package.json            # Dependencies & scripts
└── src/
    ├── main.tsx            # React root mount into #root
    ├── App.tsx             # Root desktop application & view router
    ├── index.css           # Tailwind v4 theme tokens (l1, l2, l3, d) & typography
    ├── config/
    │   └── api.ts          # Centralized API base URL & endpoint constants
    ├── constants/
    │   └── models.ts       # Model fallbacks, DEFAULT_SELECTED_MODEL, failover resolver
    ├── schemas/
    │   └── api.ts          # Zod validation schemas for backend API responses
    ├── services/
    │   └── connectivity.ts # Fetch wrappers & health check services
    ├── store/
    │   ├── panelStore.ts   # Root Zustand store composition
    │   ├── logsStore.ts    # Terminal logs entries & streaming buffer
    │   ├── themeStore.ts   # 4-mode theme state & localStorage persistence
    │   └── slices/         # 8 Feature slices
    │       ├── uiSlice.ts              # Theme, selected model, mascot skin, modals
    │       ├── chatSlice.ts            # Conversations, message feed, ReACT SSE streaming
    │       ├── analysisSlice.ts        # Paper upload, pipeline execution, reports
    │       ├── evalSlice.ts            # RAG summary metrics & benchmark runs
    │       ├── knowledgeGraphSlice.ts  # KG entities, relations, graph visualization
    │       ├── profileSlice.ts         # User profile, API keys, Ollama configuration
    │       ├── documentHistorySlice.ts # Ingested papers list & document drawer state
    │       └── hardwareSlice.ts        # CPU/GPU load & telemetry polling
    └── components/
        ├── layout/         # Header, LeftSidebar, RightSidebar, Chat/Doc history lists
        ├── features/       # Feature domain views (Chat, Analysis, Profile, Logs)
        └── ui/             # Reusable UI primitives (DropZone, ModelSelector, Wizards)
```

---

## 🧠 State Management — 8 Zustand Slices

The root store is defined in `store/panelStore.ts`, uniting 8 decoupled feature slices:

### 1. `uiSlice.ts` — UI & Preference State
- **State:** `selectedModel`, `selectedMascot`, `isSettingsOpen`, `isAuthModalOpen`.
- **Auto-Failover Sync:** Automatically synchronizes `selectedModel` when backend failover occurs via `resolveFailoverModelId()`.

### 2. `chatSlice.ts` — Chat & Streaming ReACT Trace
- **State:** `conversations`, `activeConversationId`, `messages`, `isChatGenerating`, `streamingThought`, `streamingAction`, `streamingStatus`.
- **Actions:** `sendMessage()`, `createConversation()`, `fetchMessages()`, `deleteConversation()`, `regenerateMessage()`.
- **Streaming Parser:** Decodes multi-line SSE events (`token`, `thought`, `action`, `status`, `done`, `error`) and updates UI progressively.

### 3. `analysisSlice.ts` — Paper Ingestion & Pipeline
- **State:** `papers`, `activePaperId`, `analysisStatus`, `pipelineLogs`, `reportContent`, `hyperparameters`.
- **Actions:** `uploadPaper()`, `fetchPaperHistory()`, `approvePipelineStep()`, `fetchReport()`.

### 4. `evalSlice.ts` — RAG Evaluation & Benchmarking
- **State:** `evalResults`, `isEvaluating`, `evalError`.
- **Data Models:** `RAGSummaryMetrics` (faithfulness, answer relevancy, context recall, precision, latency, token costs).
- **Actions:** `runEvaluation()`, `fetchEvalHistory()`.

### 5. `knowledgeGraphSlice.ts` — Knowledge Graph Explorer
- **State:** `nodes`, `edges`, `selectedNodeId`, `isKgLoading`, `filterCategory`.
- **Actions:** `fetchKnowledgeGraph()`, `selectNode()`, `searchEntities()`.

### 6. `profileSlice.ts` — User Profile & Credentials
- **State:** `userProfile`, `modelLimits` (live quota tracking), `ollamaConfig`.
- **Actions:** `fetchProfile()`, `updateProfile()`, `saveApiKey()`, `fetchModelLimits()`.

### 7. `documentHistorySlice.ts` — Ingested Library
- **State:** `documents`, `selectedDocumentId`, `searchQuery`.
- **Actions:** `fetchDocuments()`, `deleteDocument()`, `searchDocuments()`.

### 8. `hardwareSlice.ts` — System Hardware Telemetry
- **State:** `metrics` (CPU percentage, memory usage, GPU compute & VRAM load).
- **Actions:** `pollHardwareMetrics()`.

---

## 🎨 Feature View Highlights (`src/components/features/`)

### Analysis Feature Suite (`features/analysis/`)
- **`EvaluationDashboard.tsx`:** Visualizes RAG evaluation metrics (faithfulness, precision, cost, latency) with interactive score gauges.
- **`KnowledgeGraphPanel.tsx`:** Interactive graph canvas rendering entity nodes, concepts, and typed relationship edges extracted from research papers.
- **`ManifestViewer.tsx`:** Step-by-step pipeline execution manifest viewer inspecting tool call history, intermediate DAG states, and artifacts.
- **`ParameterConfigForm.tsx`:** Interactive approval form allowing users to inspect and adjust extracted ML hyperparameters before synthesis.
- **`ReportView.tsx`:** Rich Markdown renderer with syntax-highlighted code blocks for synthesized implementation blueprints.
- **`MilestoneTracker.tsx`:** Animated 5-phase progress stepper tracking pipeline milestones.
- **`DropZone.tsx`:** High-performance drag-and-drop file ingestion area for PDF and DOCX documents.

### Setup & Onboarding (`features/ui/`)
- **`OnboardingSetupWizard.tsx`:** Multi-step introductory wizard guiding users through API key configuration, Ollama host linking, and mascot selection.
- **`ModelSelector.tsx`:** Multi-provider model dropdown supporting Groq, OpenRouter, and Local Ollama with provider badges and active failover indicators.

---

## 🎨 4-Mode Theme System

Theme styles are declared in `src/index.css` via custom CSS tokens and applied dynamically:

- **`l1` (Warm Ivory):** Soft cream background, dark espresso typography, warm brass accent.
- **`l2` (Arctic Frost):** Cool crystalline background, slate text, ice blue accent.
- **`l3` (Iris Violet):** Lavender tinted backdrop, royal violet accent.
- **`d` (Slate Obsidian):** Deep dark slate palette with vibrant cyan and amber accents.

---

## 🔗 Related Documentation

- [Frontend Architecture Overview](../README.md) — Dual-window architecture, mascot canvas engine, and design tokens.
- [Electron App Guide](../electron_app/README.md) — Electron main process, Win32 FFI, and packaging setup.
