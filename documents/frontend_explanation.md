# 🎨 Frontend Architecture & Implementation — RUEXIS AI (Marginalia)

> Technical guide covering the Dual-Window Electron system, HTML5 Canvas Sprite Engine, React 19 + TypeScript control panel, Zustand slice architecture, and real-time SSE telemetry integration.

---

## 1. High-Level Architecture & Runtime Modes

RUEXIS AI's frontend operates in two primary modes:
1. **Desktop Native (Dual-Window Electron):** An unconstrained, frameless canvas overlay hosts the interactive mascot (*Mr. Nerdy*) floating above the OS desktop, lockstep-aligned with a dedicated slide-out React sidebar control panel.
2. **Browser Development (Vite HMR):** The React control panel runs standalone in the browser, interfacing directly with the FastAPI backend at `http://localhost:8000/api/v1`.

```mermaid
graph TD
    subgraph HostOS ["Operating System Desktop Environment"]
        MascotWindow["Desktop Mascot Overlay Window\n(Frameless · Transparent · Always-on-Top)"]
        PanelWindow["Sidebar Control Panel Window\n(Frameless · Lockstep Drag · Rounded)"]
    end

    subgraph ElectronMain ["Electron Main Process (src/main.js)"]
        WinLifecycle["Window Lifecycle & Position Engine"]
        DisplayClamp["High-DPI Display Clamping\n(125% / 150% Scale Normalization)"]
        IPCBridge["IPC Dispatcher & State Guard"]
    end

    subgraph MascotCanvas ["Mascot Stage (src/mascot.js + mascot.html)"]
        SpriteEngine["HTML5 Canvas Sprite Renderer"]
        HubRouter["Hub State Machine (Frame 0 Idle)"]
        AlphaFade["130ms Alpha Cross-Fade Engine"]
        ZzzParticles["Floating Multi-Color ZZZ Keyframes"]
    end

    subgraph ReactApp ["React 19 Control Panel (renderer/src/)"]
        AppRoot["App.tsx & Panel.tsx"]
        ZustandStore["Zustand State Engine (8 Slices)"]
        SSEListener["SSE Stream Ingestion (connectivity.ts)"]
    end

    subgraph BackendAPI ["FastAPI Backend (:8000/api/v1)"]
        UploadEP["/papers/upload"]
        PipelineSSE["/pipeline/jobs/{id}/events"]
        ChatEP["/conversations/{id}/chat"]
        ModelEP["/models/limits"]
    end

    PanelWindow -->|Hosts Bundle| ReactApp
    MascotWindow -->|Hosts Canvas| MascotCanvas
    ReactApp -- "window.mascotAPI (preload.js)" --> IPCBridge
    MascotCanvas -- "IPC drag & click events" --> IPCBridge
    IPCBridge <--> WinLifecycle
    WinLifecycle --> DisplayClamp
    WinLifecycle -. Lockstep Coordinate Sync .-> PanelWindow
    ReactApp -- "Fetch / Multipart" --> BackendAPI
    BackendAPI -- "SSE Telemetry Streams" --> SSEListener
    SSEListener --> ZustandStore
```

---

## 2. Electron Main Process & Native IPC Bridge

The Electron layer (`frontend/electron_app/src/main.js` and `preload.js`) coordinates multi-window positioning, High-DPI display scaling, and secure inter-process communication without exposing raw Node.js primitives to the renderer.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Mascot as Mascot Canvas Window
    participant Main as Electron Main (main.js)
    participant Panel as React Panel (renderer)
    participant Backend as FastAPI Backend

    User->>Mascot: Clicks Mr. Nerdy (Sleep / Idle Pose)
    Mascot->>Main: IPC send('toggle-panel')
    Main->>Main: Calculate bounds (+16px vertical head offset)
    Main->>Panel: Show window & emit('state-change', 'idle')
    Panel->>Panel: Rehydrate profile, papers & conversations

    User->>Panel: Drag & drop PDF academic paper
    Panel->>Backend: POST /api/v1/papers/upload
    Panel->>Main: mascotAPI.setMascotState('catching')
    Main->>Mascot: IPC emit('state-change', 'hunch')
    Mascot->>Mascot: Transition to Typing Hunch pose

    Backend-->>Panel: SSE Event: 'node_started' / 'node_completed'
    Panel->>Panel: Update MilestoneTracker & ReAct accordion
    
    Backend-->>Panel: SSE Event: 'pipeline_completed'
    Panel->>Main: mascotAPI.setMascotState('idle')
    Main->>Mascot: IPC emit('state-change', 'idle')
    Mascot->>Mascot: Cross-fade to Standing pose

    User->>Mascot: Drag Mr. Nerdy across desktop
    Mascot->>Main: IPC send('drag-window', {deltaX, deltaY})
    Main->>Panel: setPosition(panelX + deltaX, panelY + deltaY)
    Main->>Main: Clamp window dimensions against DPI scaling
```

### Preload IPC API Surface (`window.mascotAPI`)

```mermaid
classDiagram
    class MascotAPI {
        +getPathForFile(file: File) string
        +setIgnoreMouseEvents(ignore: boolean, options: any) void
        +dragWindow(delta: object) void
        +dragEnd() void
        +togglePanel() void
        +uploadPDF(filePath, type, modelName) void
        +triggerUpload(filename, filePath, type, modelName) void
        +toggleMaximize() void
        +setMascotState(state: string) void
        +reportUserActivity() void
        +setMascotSkin(skinId: string) void
        +getMascotSkin() Promise~string~
        +onStateChange(cb: fn) void
        +onPipelineLog(cb: fn) void
        +onPipelineCompleted(cb: fn) void
        +onMaximizeChange(cb: fn) void
        +onMascotSkinChange(cb: fn) void
    }
```

---

## 3. Mascot Canvas Sprite Engine (`mascot.js`)

The mascot engine renders animated sprite strips using an HTML5 Canvas without framework overhead. Transitions between different emotional states flow through a **Hub Pose State Machine** centered on Frame `0` of the idle pose.

```mermaid
stateDiagram-v2
    [*] --> Sleeping: App Launch / Idle Timeout

    Sleeping --> Idle: Click / Panel Opened
    Idle --> Sleeping: Panel Closed / Inactivity

    Idle --> Hunch: Pipeline Processing / Ingestion
    Hunch --> Idle: Task Completed

    Idle --> Thinking: ReAct Chat Generation
    Thinking --> Idle: Response Stream Finished

    Idle --> Excite: Milestone Success / Blueprint Generated
    Excite --> Idle: Cooldown (2000ms)

    Idle --> Angry: API Failure / Quota Exhaustion
    Angry --> Idle: Reset / User Action

    Idle --> Catching: File Dragged Over Panel
    Catching --> Hunch: File Dropped & Uploaded

    note right of Idle
        Central Hub Routing:
        Every state switch unwinds
        to Frame 0 of Idle before
        playing target animation.
    end note
```

### Cross-Fading & State Queue Pipeline

```mermaid
flowchart LR
    A[Incoming State Change] --> B{Animation Playing?}
    B -->|Yes| C[Buffer in pendingTargetState Queue]
    B -->|No| D[Resolve Path via Hub Frame 0]
    C -->|Frame Finished| D
    D --> E[Step Interpolator: 6 Sub-steps]
    E --> F[130ms Canvas globalAlpha Cross-Fade]
    F --> G[Render Frame to Offscreen Canvas]
    G --> H[Draw to Screen Canvas Context]
```

---

## 4. React Control Panel Layout Hierarchy

The React application entry point is `App.tsx`, which mounts `Panel.tsx`. The interface adapts between a **compact floating drawer (340x480)** and a **maximized full-screen IDE dashboard (1400x900)**.

```mermaid
graph TD
    App["App.tsx"] --> Panel["Panel.tsx (Main Control Shell)"]
    
    Panel --> DragDropOverlay["ui/DragDropOverlay.tsx\n(Full-bleed drop indicator)"]
    Panel --> Header["layout/Header.tsx\n(Brand · ModelSelector · Maximizer · Controls)"]
    
    Panel --> BodyFrame["Flex Row Workspace"]
    
    BodyFrame --> LeftSidebar["layout/LeftSidebar.tsx\n(Collapsible 56px Rail ↔ 260px Drawer)"]
    LeftSidebar --> MascotBox["layout/MascotBox.tsx (Avatar box)"]
    LeftSidebar --> ChatHistory["layout/ChatHistoryList.tsx"]
    LeftSidebar --> UserProfileCard["layout/UserProfileCard.tsx"]

    BodyFrame --> MainContent["main (Center Workspace)"]
    
    MainContent --> ViewSwitch{"activeView Router"}
    ViewSwitch -->|chat| ChatStage["Chat & Analysis Stage"]
    ViewSwitch -->|profile| UserProfileView["features/profile/UserProfile.tsx"]
    ViewSwitch -->|pdf-viewer| PdfViewer["features/analysis/PdfViewerPage.tsx"]

    ChatStage --> MessageFeed["features/chat/MessageFeed.tsx"]
    MessageFeed --> MessageBubble["features/chat/MessageBubble.tsx"]
    MessageBubble --> ReActAccordion["features/chat/ReActStepsAccordion.tsx"]
    MessageBubble --> InlineAnalysis["Inline Analysis & Reports"]
    
    ChatStage --> StickyBottom["Sticky Dock Container"]
    StickyBottom --> ChatInputArea["features/chat/ChatInputArea.tsx\n(Prompt input · File browse · Send)"]
    StickyBottom --> FooterDisclaimer["Branding & Latency Notice"]

    MainContent --> LogsDrawer["features/logs/LogsDrawer.tsx\n(Slide-up terminal)"]
    MainContent --> DocumentsDrawer["features/analysis/DocumentsDrawer.tsx\n(Compact-mode document drawer)"]

    BodyFrame --> RightSidebar["layout/RightSidebar.tsx\n(Maximized-only Paper Metadata Drawer)"]
    RightSidebar --> DocumentHistoryList["layout/DocumentHistoryList.tsx"]

    Panel --> LocalAuthModal["ui/LocalAuthModal.tsx\n(Developer onboarding modal)"]
```

---

## 5. Feature Modules Deep Dive

### 5.1 Chat & ReAct Stream Processing

When chatting with the assistant, incoming reasoning traces containing `<thought>`, `Action:`, and `Observation:` blocks are parsed on the fly.

```mermaid
flowchart TD
    RawContent[LLM Response Stream Content] --> Parser["parseReAct.ts\n(Regex Step Tokenizer)"]
    
    Parser --> ThoughtBlock["💭 Thought: Agent Plan & Reasoning"]
    Parser --> ActionBlock["⚡ Action: Tool Invocation (e.g. rag_search)"]
    Parser --> ObsBlock["🔍 Observation: Tool Output & Excerpts"]
    Parser --> FinalAnswer["📝 Final Synthesis Response"]

    ThoughtBlock --> Accordion["ReActStepsAccordion.tsx\n(Collapsible execution trace)"]
    ActionBlock --> Accordion
    ObsBlock --> Accordion
    FinalAnswer --> Markdown["MarkdownRenderer (Code blocks, Math, Tables)"]
```

### 5.2 Analysis & Pipeline Feature Stack

```mermaid
graph LR
    subgraph IngestionStage ["Ingestion & Tracking"]
        DZ["DropZone.tsx\n(PDF/DOCX)"]
        MT["MilestoneTracker.tsx\n(5-Stage Animated Progress)"]
        TS["TierSelector.tsx\n(Brief / Detailed / Full)"]
    end

    subgraph SynthesisStage ["Synthesis & Config"]
        PCF["ParameterConfigForm.tsx\n(Interactive extraction overrides)"]
        MV["ManifestViewer.tsx\n(JSON Execution Ledger)"]
        ED["EvaluationDashboard.tsx\n(Faithfulness & Hallucination Gauges)"]
    end

    subgraph DeepExploration ["Exploration Views"]
        RV["ReportView.tsx\n(Markdown Blueprint Exporter)"]
        KGP["KnowledgeGraphPanel.tsx\n(7-Tier Interactive Node Graph)"]
        PDFV["PdfViewerPage.tsx\n(Side-by-side Page Renderer)"]
    end

    DZ --> MT --> PCF --> RV
    MT --> ED
    MT --> MV
    RV --> KGP
    RV --> PDFV
```

---

## 6. Zustand Store Architecture (Slice Pattern)

The frontend consolidates all reactive application state in `usePanelStore` using Zustand's slice composition pattern, complemented by standalone stores for terminal logs and themes.

```mermaid
graph TD
    PanelStore["usePanelStore (store/panelStore.ts)"]

    subgraph Slices ["Composable Zustand Slices (store/slices/)"]
        UISlice["uiSlice.ts\n• activeView\n• isPanelOpen\n• isMaximized\n• stagedFile"]
        ProfileSlice["profileSlice.ts\n• userId, username\n• apiKeys (gemini, openai)\n• ollamaConfig\n• avatarSkin"]
        ChatSlice["chatSlice.ts\n• messages list\n• activeConversationId\n• isChatGenerating\n• thread history"]
        AnalysisSlice["analysisSlice.ts\n• currentJobId, paperId\n• milestones & progress\n• decompScores\n• blueprintReport"]
        DocHistorySlice["documentHistorySlice.ts\n• uploadedPapers list\n• selectedPaperId\n• paper metadata"]
        HardwareSlice["hardwareSlice.ts\n• cpuPercent, ramPercent\n• vramUsage, gpuTemp\n• activeProviderStatus"]
        KGSlice["knowledgeGraphSlice.ts\n• graphNodes & edges\n• selectedNodeId\n• tierFilters"]
        EvalSlice["evalSlice.ts\n• ragBenchmarkResults\n• hallucinationMetric\n• verificationRatio"]
    end

    PanelStore --- UISlice
    PanelStore --- ProfileSlice
    PanelStore --- ChatSlice
    PanelStore --- AnalysisSlice
    PanelStore --- DocHistorySlice
    PanelStore --- HardwareSlice
    PanelStore --- KGSlice
    PanelStore --- EvalSlice

    subgraph StandaloneStores ["Independent State Stores"]
        LogsStore["useLogsStore (store/logsStore.ts)\n• terminalLogs array\n• addLog(msg, level)\n• clearLogs()"]
        ThemeStore["useThemeStore (store/themeStore.ts)\n• currentTheme (dark/light)\n• toggleTheme()"]
    end
```

---

## 7. Real-Time Telemetry & Backend Integration

The communication service layer (`renderer/src/services/connectivity.ts`) and API configuration (`renderer/src/config/api.ts`) handle REST operations and consume Server-Sent Events (SSE).

```mermaid
flowchart TD
    subgraph FrontendService ["connectivity.ts (Service Layer)"]
        InitSSE["streamExtraction(jobId, onLog, onComplete, onFail)"]
        ESInstance["EventSource(/api/v1/pipeline/jobs/{id}/events)"]
    end

    subgraph EventStream ["SSE Channel Events"]
        E1["event: node_started"]
        E2["event: node_completed"]
        E3["event: refinement / retry"]
        E4["event: mascot_state"]
        E5["event: pipeline_completed"]
        E6["event: pipeline_failed / error"]
    end

    subgraph StoreDispatch ["Zustand Store Actions"]
        D1["addLog('[Node] ...')\nsetMilestoneActive(nodeId)"]
        D2["setMilestoneCompleted(nodeId)\nupdateProgress(pct)"]
        D3["addLog('[Self-Healing] Retry...')"]
        D4["window.mascotAPI.setMascotState(state)"]
        D5["setReport(reportContent)\nsetMascotState('idle')\ncloseSSE()"]
        D6["setError(errorMsg)\nsetMascotState('angry')\ncloseSSE()"]
    end

    InitSSE --> ESInstance
    ESInstance --> E1 & E2 & E3 & E4 & E5 & E6
    E1 --> D1
    E2 --> D2
    E3 --> D3
    E4 --> D4
    E5 --> D5
    E6 --> D6
```

---

## 8. Theme System & Design Tokens

Tailwind v4 tokens in `renderer/src/index.css` define an academic, archival aesthetic:

```mermaid
classDiagram
    class MarginaliaThemeTokens {
        --color-ink : #1A1B20 (Deep archival dark)
        --color-parchment : #EDE6D6 (Warm paper surface)
        --color-brass : #C99A3E (Primary gold accent)
        --color-confirmed : #6B9B7C (Verified green)
        --color-inferred : #D9A441 (Extracted amber)
        --color-assumed : #8B8378 (Assumed gray)
        --color-error : #B5533C (Alert terracotta)
        --font-serif : "Fraunces" (Display headlines)
        --font-mono : "IBM Plex Mono" (Code & traces)
        --font-sans : "Space Grotesk" (UI navigation)
    }
```

---

## 9. Comprehensive Frontend File Reference Table

### Electron Main Process & Mascot Canvas (`frontend/electron_app/`)

| File Path | Description | Tech Stack |
|---|---|---|
| `electron_app/src/main.js` | Electron main process: manages dual-window lifecycle, DPI scaling clamp, lockstep drag coordinates, and IPC event dispatching. | Node.js / Electron |
| `electron_app/src/preload.js` | Secure preload script exposing `window.mascotAPI` methods to the renderer context via `contextBridge`. | Electron ContextBridge |
| `electron_app/src/mascot.js` | High-performance HTML5 Canvas sprite engine with hub state machine, 130ms alpha cross-fading, and event queues. | Vanilla JS / Canvas 2D |
| `electron_app/src/mascot.html` | Frameless window container DOM hosting the sprite canvas and floating ZZZ particles. | HTML5 |
| `electron_app/src/mascot.css` | Transparent canvas positioning, cursor styling, and multi-color ZZZ keyframe animations. | CSS3 Keyframes |
| `electron_app/src/mascot_transitions.json`| Sprite frame coordinates, animation timing curves, and state transition maps. | JSON Schema |
| `electron_app/src/assets/` | Transparent PNG sprite strips for Mr. Nerdy poses (`stand_sleep`, `stand_to_hunch`, `stand_to_angry`, etc.). | Asset Directory |

### React Sidebar Control Panel (`frontend/renderer/src/`)

| File Path | Description | Tech Stack |
|---|---|---|
| `renderer/src/main.tsx` | React 19 entrypoint mounting `App.tsx` into the root DOM element. | React 19 / TSX |
| `renderer/src/App.tsx` | Top-level container providing root theme classes and rendering `Panel.tsx`. | React / TSX |
| `renderer/src/index.css` | Tailwind v4 configuration, font imports (Fraunces, Space Grotesk, IBM Plex Mono), theme variables, and custom scrollbars. | CSS3 / Tailwind v4 |
| `renderer/src/config/api.ts` | Dynamic API URL resolver and endpoint constant catalog (supports Electron `localhost:8000` & Vite dev mode). | TypeScript |
| `renderer/src/services/connectivity.ts`| Backend communications service: handles REST calls and manages SSE EventSource listeners. | TypeScript / Fetch / SSE |
| `renderer/src/constants/branding.ts` | Product brand strings, disclaimer notices, and mascot naming constants. | TypeScript |
| `renderer/src/constants/models.ts` | Default catalog of supported LLM / VLM engines, context limits, and routing tier tags. | TypeScript |
| `renderer/src/utils/markdownParser.tsx` | Custom markdown renderer supporting code syntax highlighting, math formulas, and tables. | React / TSX |
| `renderer/src/utils/formatters.ts` | Formatting helpers for file sizes, timestamps, execution runtimes, and confidence percentages. | TypeScript |

### Layout Components (`renderer/src/components/layout/`)

| File Path | Description | Tech Stack |
|---|---|---|
| `components/layout/Header.tsx` | Unified top bar hosting brand icon, ModelSelector dropdown, theme switch, log drawer toggle, and window controls. | React / TSX |
| `components/layout/LeftSidebar.tsx` | Collapsible sidebar: toggles between 56px icon rail and 260px expanded drawer with chat threads and paper history. | React / TSX |
| `components/layout/RightSidebar.tsx` | Maximized-mode slide-out drawer presenting detailed paper metadata, citation badges, and document attributes. | React / TSX |
| `components/layout/MascotBox.tsx` | Interactive companion card showing active skin, animated pulse indicator, and mood status badge. | React / TSX |
| `components/layout/ChatHistoryList.tsx` | Interactive list of active and archived conversation threads with rename and delete options. | React / TSX |
| `components/layout/DocumentHistoryList.tsx`| Ingested paper ledger with decomposition scores, parameter certainty gauges, and delete actions. | React / TSX |
| `components/layout/UserProfileCard.tsx` | Compact user profile chip displaying developer avatar, username, and local status. | React / TSX |
| `components/layout/CompactHistoryDropdown.tsx`| Minimized-mode quick switcher for jumping between past analysis sessions. | React / TSX |

### Feature Modules (`renderer/src/components/features/`)

| File Path | Description | Tech Stack |
|---|---|---|
| `components/panel/Panel.tsx` | Core container coordinating layout panes, drag-and-drop ingestion, view routing, and IPC rehydration. | React / TSX |
| `features/chat/MessageFeed.tsx` | Infinite-scrolling conversation feed with auto-scroll and message role segmentation. | React / TSX |
| `features/chat/MessageBubble.tsx` | Chat speech bubble rendering Markdown, inline attachments, ReAct accordions, and model attribution chips. | React / TSX |
| `features/chat/ChatInputArea.tsx` | Auto-expanding textarea with file attachment staging, model selector triggers, and keyboard shortcuts. | React / TSX |
| `features/chat/parseReAct.ts` | Regex tokenizer isolating thoughts, actions, and observations from streaming responses. | TypeScript |
| `features/chat/ReActStepsAccordion.tsx` | Expandable disclosure UI presenting agent reasoning steps, tool queries, and raw observations. | React / TSX |
| `features/analysis/DropZone.tsx` | Drag-and-drop zone with animated scanline styling for PDF/DOCX paper ingestion. | React / TSX |
| `features/analysis/MilestoneTracker.tsx` | Animated 5-step milestone pipeline visualizer showing real-time backend agent progress. | React / TSX |
| `features/analysis/ReportView.tsx` | Rich blueprint proposal reader with copy-to-clipboard, export buttons, and section jumps. | React / TSX |
| `features/analysis/ParameterConfigForm.tsx`| Interactive form allowing manual tuning and overrides of extracted hyper-parameters. | React / TSX |
| `features/analysis/EvaluationDashboard.tsx`| RAG benchmark analytics dashboard with radar graphs, hallucination rates, and faithfulness scores. | React / TSX |
| `features/analysis/KnowledgeGraphPanel.tsx`| Interactive 7-tier knowledge graph visualizing entities, dependencies, and methods extracted from the paper. | React / TSX / Canvas |
| `features/analysis/ManifestViewer.tsx` | Structured JSON inspection viewer for reviewing the execution ledger and node timestamps. | React / TSX |
| `features/analysis/PdfViewerPage.tsx` | Side-by-side embedded PDF reader with jump-to-page and section highlighter. | React / TSX |
| `features/analysis/DocumentsDrawer.tsx` | Slide-up drawer for accessing previously processed papers in compact view mode. | React / TSX |
| `features/logs/LogsDrawer.tsx` | Expandable terminal console displaying live backend execution logs, log levels, and clear controls. | React / TSX |
| `features/profile/UserProfile.tsx` | Developer profile dashboard for managing API keys, Ollama endpoints, quota gauges, and mascot skins. | React / TSX |
| `features/profile/ApiKeysConfigSection.tsx`| Form for verifying and storing Gemini, OpenAI, Anthropic, and Groq API tokens. | React / TSX |
| `features/profile/OllamaConfigSection.tsx` | Local inference connectivity validator checking status, models, and latency of Ollama instances. | React / TSX |
| `features/profile/ModelLimitsSection.tsx` | Daily quota usage meters showing remaining calls and resets for cloud providers. | React / TSX |
| `features/profile/MascotSelector.tsx` | Visual skin picker for switching between mascot avatars (Mr. Nerdy, Robo, etc.). | React / TSX |

### State Management Stores (`renderer/src/store/`)

| File Path | Description | Tech Stack |
|---|---|---|
| `store/panelStore.ts` | Central Zustand store assembling all 8 feature slices into a single unified reactive state hook. | Zustand / TS |
| `store/slices/uiSlice.ts` | Manages view state (`chat`, `profile`, `pdf-viewer`), modal visibility, sidebar states, and staged files. | Zustand Slice |
| `store/slices/chatSlice.ts` | Manages messages, active conversation ID, chat generation state, and message dispatch. | Zustand Slice |
| `store/slices/analysisSlice.ts` | Manages job lifecycle, pipeline milestones, decomposition certainty scores, and blueprint reports. | Zustand Slice |
| `store/slices/profileSlice.ts` | Manages user credentials, API keys, Ollama configuration, and active mascot avatar. | Zustand Slice |
| `store/slices/documentHistorySlice.ts`| Manages paper document ledger, search filtering, and active document selection. | Zustand Slice |
| `store/slices/hardwareSlice.ts` | Manages real-time telemetry: CPU, RAM, GPU VRAM, temperature, and backend provider health. | Zustand Slice |
| `store/slices/knowledgeGraphSlice.ts`| Manages knowledge graph node filters, active entity selection, and tier visibility. | Zustand Slice |
| `store/slices/evalSlice.ts` | Manages RAG evaluation benchmarks, faithfulness scores, and hallucination metrics. | Zustand Slice |
| `store/logsStore.ts` | Independent store for real-time terminal logs with log level filtering and capacity limits. | Zustand |
| `store/themeStore.ts` | Independent store tracking light/dark themes and persisting preferences to `localStorage`. | Zustand |
