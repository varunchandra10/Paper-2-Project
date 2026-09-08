# RUEXIS AI — Detailed System Architectures & Flow Guide

> **Project Name:** RUEXIS AI (Research Understanding & EXecution Intelligence System)  
> **Document Purpose:** Complete structural and flow architecture of RUEXIS AI broken down into standalone modular divisions, culminating in an integrated end-to-end master architecture.

---

## 📑 Table of Contents
1. [Architecture Philosophy & Divisional Design](#1-architecture-philosophy--divisional-design)
2. [Division 1: Desktop Shell & Native Win32 Subsystem](#2-division-1-desktop-shell--native-win32-subsystem)
3. [Division 2: Mascot Interactive Sprite Engine & 13-State FSM](#3-division-2-mascot-interactive-sprite-engine--13-state-fsm)
4. [Division 3: Frontend UI, State Management & SSE Consumer](#4-division-3-frontend-ui-state-management--sse-consumer)
5. [Division 4: Backend FastAPI Bridge & Service Layer](#5-division-4-backend-fastapi-bridge--service-layer)
6. [Division 5: Agentic Ingestion & LangGraph Processing Pipeline](#6-division-5-agentic-ingestion--langgraph-processing-pipeline)
7. [Division 6: Intelligent Model Router & Fallback Cascade](#7-division-6-intelligent-model-router--fallback-cascade)
8. [Master Synthesis: Complete Integrated End-to-End Architecture](#8-master-synthesis-complete-integrated-end-to-end-architecture)

---

## 1. Architecture Philosophy & Divisional Design

RUEXIS AI is structured as a **modular multi-tier desktop intelligence platform**. To ensure clarity and maintainability, the system is decomposed into **6 specialized functional divisions**. Each division operates with well-defined boundaries, protocols, and data contracts. The final master architecture combines all 6 divisions into a synchronized, real-time reactive loop.

```mermaid
flowchart TD
    subgraph Divisions["Modular Divisions"]
        D1["Division 1: Desktop Shell & Win32 FFI"]
        D2["Division 2: Mascot Engine & 13-State FSM"]
        D3["Division 3: Frontend UI & Zustand State"]
        D4["Division 4: FastAPI Bridge & Service Layer"]
        D5["Division 5: LangGraph Agentic Pipeline"]
        D6["Division 6: Model Router & Fallback"]
    end

    Divisions --> Master["Division 7: Master Integrated Architecture (End-to-End Synthesis)"]
```

---

## 2. Division 1: Desktop Shell & Native Win32 Subsystem

### 2.1 Overview
The desktop shell is built on **Electron** and interacts directly with the **Windows Win32 API** using `koffi` (C-level Foreign Function Interface). It creates and coordinates two distinct transparent windows without standard OS borders or title bars.

### 2.2 Component Architecture Diagram

```mermaid
flowchart TB
    subgraph Win32_OS["Windows 11 / 10 OS Layer"]
        Taskbar["Windows Taskbar (Shell_TrayWnd)"]
        Display["Display Monitor Work Area"]
        UserMouse["User Mouse & Keyboard Events"]
    end

    subgraph Electron_Main["Electron Main Process (main.ts)"]
        FFI["Koffi Win32 FFI Bridge<br/>• SHAppBarMessage(ABM_GETTASKBARPOS)<br/>• APPBARDATA struct parser"]
        WinManager["Window Manager Lifecycle Controller"]
        IPCMain["IPC Main Event Dispatcher"]
        
        FFI -->|Query Position & Height| Taskbar
        WinManager -->|Calculate Geometry| Display
    end

    subgraph Windows["Dual Transparent Windows"]
        subgraph Mascot_Window["Mascot Window (Renderer 1)"]
            MascotCanvas["Always-On-Top Viewport<br/>128x128 Transparent Canvas"]
        end
        subgraph Sidebar_Window["Sidebar Window (Renderer 2)"]
            SidebarUI["Docked Glassmorphic UI<br/>420px Width Viewport"]
        end
    end

    WinManager -->|Position above taskbar| MascotCanvas
    WinManager -->|Right-screen dock| SidebarUI
    IPCMain <-->|IPC Channels| MascotCanvas
    IPCMain <-->|IPC Channels| SidebarUI
```

### 2.3 Key Operational Flows
1. **Taskbar Geometry Auto-Discovery:**
   - Calls `SHAppBarMessage` with `ABM_GETTASKBARPOS` via `koffi`.
   - Computes taskbar edge (Bottom, Top, Left, Right) and height/width.
   - Positions the Mascot Window precisely 12px above the active taskbar edge.
2. **IPC Communication Channels:**
   - `mascot:set-state`: Updates current mascot animation state.
   - `window:toggle-sidebar`: Expands or collapses the right-docked sidebar.
   - `app:minimize` / `app:quit`: Standard desktop lifecycle events.

---

## 3. Division 2: Mascot Interactive Sprite Engine & 13-State FSM

### 3.1 Overview
The companion mascot is an interactive desktop sprite driven by a deterministic **13-State Finite State Machine (FSM)**. It renders animated PNG sprite sheets on an HTML5 canvas and changes animations based on AI pipeline events, user clicks, and inactivity timers.

### 3.2 13-State FSM Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> sleeping: App Startup
    sleeping --> waking: User Clicks Mascot
    waking --> idle: Wake Animation Complete
    
    idle --> blinking: Random Timer (3-8s)
    blinking --> idle: Blink Complete (4 frames)
    
    idle --> waving: User Click / Welcome
    waving --> idle: Wave Complete
    
    idle --> reading: Ingestion Started
    reading --> thinking: Agent Reason / Extraction
    thinking --> writing: Summary / Report Streaming
    writing --> celebrating: Analysis Complete
    celebrating --> idle: 5s Elapsed
    
    idle --> tired: Inactivity (120s)
    tired --> sleeping: Inactivity (300s)
    
    idle --> searching: Chat Query Dispatched
    searching --> talking: LLM Token Streaming
    talking --> idle: Stream End
    
    idle --> error: Backend Error / Quota Exhausted
    error --> idle: User Dismiss / Retry
```

### 3.3 Sprite Engine Specs
| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **Grid Size** | 128 × 128 px | Transparent background |
| **Frame Rates** | 8 FPS – 16 FPS | State-dependent (idle: 8fps, talking: 14fps) |
| **Audio Sync** | Web Audio API | Micro-chirps on wave, click, and celebrate |
| **Triggers** | SSE Events & Mouse | Direct mapping to backend pipeline states |

---

## 4. Division 3: Frontend UI, State Management & SSE Consumer

### 4.1 Overview
The frontend is built with **React 19**, **Vite**, and **Tailwind CSS** featuring a deep glassmorphism design system. Global client state is centralized in modular **Zustand stores**, receiving real-time streaming updates from the backend via a resilient **Server-Sent Events (SSE)** client.

### 4.2 State & Component Hierarchy Diagram

```mermaid
flowchart TD
    subgraph UI_Components["React 19 View Layer"]
        Header["Header & Mode Switcher<br/>(Light / Dark / OLED Themes)"]
        Dropzone["PDF Ingestion Zone<br/>(Drag-and-Drop + File Browser)"]
        DocViewer["Paper Reader & Tabbed Analysis<br/>(Summary, Deep Dive, Code, Math)"]
        ChatPanel["Interactive Chat Drawer<br/>(Context-Aware Paper QA)"]
        MetricsBar["Hardware & Quota Monitor<br/>(CPU, RAM, GPU, API Limits)"]
    end

    subgraph Zustand_Stores["Zustand State Layer"]
        MascotStore["useMascotStore<br/>• currentState (13 states)<br/>• speechBubble<br/>• isHovered"]
        PaperStore["usePaperStore<br/>• activePaper<br/>• analysisResults<br/>• extractionProgress"]
        ChatStore["useChatStore<br/>• messages<br/>• tokenBuffer<br/>• isStreaming"]
        SystemStore["useSystemStore<br/>• hardwareTelemetry<br/>• providerQuotas<br/>• activeTheme"]
    end

    subgraph SSE_Consumer["SSE Stream Service"]
        EventSource["EventSource / Fetch Stream<br/>/stream/{run_id}"]
        EventParser["SSE Event Dispatcher<br/>• step_progress<br/>• token_chunk<br/>• error_event"]
    end

    SSE_Consumer -->|Dispatches Events| Zustand_Stores
    Zustand_Stores -->|Reactive Bindings| UI_Components
```

### 4.3 Key UI Capabilities
- **Glassmorphic Theme Engine:** Dynamic switching between Dark Indigo, Obsidian OLED, and Frost Light with backdrop blurs (`backdrop-blur-xl`).
- **Interactive Markdown & Math Rendering:** `react-markdown` with `KaTeX` for equations and `Prism` for syntax-highlighted code.
- **Optimistic State Updates:** Instant UI response on user prompts while streaming token deltas.

---

## 5. Division 4: Backend FastAPI Bridge & Service Layer

### 5.1 Overview
The backend is a high-performance **FastAPI (Python 3.11+)** server that acts as the communication and orchestration bridge between the desktop client and AI computation graph.

### 5.2 Service Architecture Diagram

```mermaid
flowchart TB
    subgraph Client_Requests["Inbound HTTP / SSE Calls"]
        ReqAnalyze["POST /analyze<br/>(PDF Upload / File Path)"]
        ReqChat["POST /chat<br/>(Paper QA Context Query)"]
        ReqHardware["GET /hardware<br/>(System Telemetry)"]
        ReqStream["GET /stream/{run_id}<br/>(Live SSE Event Channel)"]
    end

    subgraph FastAPI_Bridge["FastAPI Application Core"]
        Router["APIRouter Layer"]
        CORS["CORS & Security Middleware"]
        SessionManager["In-Memory Run Manager<br/>(Dict[run_id, AsyncQueue])"]
        HardwareWorker["Background Telemetry Poller<br/>(psutil / GPUtil)"]
    end

    subgraph Downstream_Services["Internal Execution Engines"]
        DocIngest["Docling / PyMuPDF Extractor"]
        LangGraphEng["LangGraph StateGraph Engine"]
        LLMRouter["Multi-Provider LLM Router"]
    end

    ReqAnalyze --> Router
    ReqChat --> Router
    ReqHardware --> Router
    ReqStream --> Router

    Router --> SessionManager
    Router --> HardwareWorker
    Router --> DocIngest
    Router --> LangGraphEng
    Router --> LLMRouter

    SessionManager -->|Streams Events| ReqStream
```

### 5.3 API Endpoints Specification
- `POST /analyze`: Accepts PDF upload or local path, registers a new `run_id`, spawns asynchronous LangGraph execution.
- `GET /stream/{run_id}`: Yields real-time Server-Sent Events (`event: step_progress`, `event: result`, `event: error`).
- `POST /chat`: Context-aware conversational endpoint connected to extracted paper chunks.
- `GET /hardware`: Returns CPU %, RAM usage, and GPU VRAM statistics.
- `GET /health`: Health check and provider connectivity status.

---

## 6. Division 5: Agentic Ingestion & LangGraph Processing Pipeline

### 6.1 Overview
Document processing and research comprehension are governed by a **LangGraph StateGraph**. The pipeline extracts unstructured text, tables, and equations from PDFs, then routes the structured content through specialized analytical agent nodes.

### 6.2 LangGraph Execution Graph Diagram

```mermaid
flowchart TD
    Start([Start: Ingest PDF]) --> ExtractNode["Docling / PyMuPDF Node<br/>• Text & Table Extraction<br/>• OCR Fallback if Scanned"]
    
    ExtractNode --> ChunkNode["Semantic Section Splitter<br/>• Abstract, Methods, Math, Results"]
    
    ChunkNode --> StructureNode["Structure Analysis Agent<br/>• Validates Schema & Hierarchy"]
    
    StructureNode --> ParallelBranch{"Parallel Analysis"}
    
    ParallelBranch --> ExecSummary["Executive Summary Node<br/>(Cerebras / Groq Flash)"]
    ParallelBranch --> DeepTechnical["Deep Tech Extraction Node<br/>(Gemini 2.5 / DeepSeek R1)"]
    ParallelBranch --> MathVerify["Formula & Code Node<br/>(Qwen 2.5 Coder)"]
    
    ExecSummary --> ConsolidateNode["Synthesis & Critique Node<br/>• Reconciles Insights<br/>• Generates Actionable Insights"]
    DeepTechnical --> ConsolidateNode
    MathVerify --> ConsolidateNode
    
    ConsolidateNode --> EmitFinal["Save to Session & Emit Complete"]
    EmitFinal --> EndNode([End: Ready for Chat])
```

### 6.3 State Schema (`AgentState`)
```python
class AgentState(TypedDict):
    run_id: str
    paper_path: str
    extracted_text: str
    sections: dict[str, str]
    tables: list[dict]
    formulas: list[str]
    executive_summary: str
    deep_dive_analysis: str
    code_artifacts: list[str]
    progress_percentage: int
    current_status: str
```

---

## 7. Division 6: Intelligent Model Router & Fallback Cascade

### 7.1 Overview
RUEXIS AI uses a **Dual-Engine Intelligent Model Router** connected to 5 external LLM providers. It guarantees zero downtime by tracking live quotas and automatically falling back to alternative providers when rate limits (HTTP 429) or timeouts occur.

### 7.2 Router Decision & Fallback Flowchart

```mermaid
flowchart TD
    InboundPrompt([Inbound Agent / Chat Prompt]) --> AnalyzeComplexity{"Analyze Prompt Type"}
    
    AnalyzeComplexity -->|Speed / Streaming / Chat| SpeedTier["Speed Tier (High TPS)"]
    AnalyzeComplexity -->|Deep Tech / Math / Reasoning| DeepTier["Deep Reasoning Tier"]

    subgraph Speed_Cascade["Speed Tier Fallback Cascade"]
        SpeedTier --> C1["1. Cerebras (Llama 3.3 70B @ 2000+ tps)"]
        C1 -->|429 / Error| G1["2. Groq (Llama 3.3 70B / 8B Instant)"]
        G1 -->|429 / Error| Gem1["3. Google Gemini (Gemini 2.5 Flash)"]
        Gem1 -->|429 / Error| HF1["4. HuggingFace Serverless"]
        HF1 -->|429 / Error| OR1["5. OpenRouter Free Tier"]
    end

    subgraph Deep_Cascade["Deep Reasoning Fallback Cascade"]
        DeepTier --> Gem2["1. Google Gemini (Gemini 2.5 Pro / Flash)"]
        Gem2 -->|429 / Error| HF2["2. HuggingFace (Qwen 2.5 Coder 32B)"]
        HF2 -->|429 / Error| G2["3. Groq (DeepSeek R1 Distill)"]
        G2 -->|429 / Error| C2["4. Cerebras (Llama 3.3 70B)"]
        C2 -->|429 / Error| OR2["5. OpenRouter Fallback"]
    end

    Speed_Cascade --> QuotaTrack["Live Quota & Usage Tracker<br/>(Tracks remaining TPM / RPM)"]
    Deep_Cascade --> QuotaTrack
    QuotaTrack --> OutboundResult([Return Token Stream / Response])
```

### 7.3 Multi-Provider Configuration Matrix
| Provider | Primary Models | Latency / Speed | Purpose |
| :--- | :--- | :--- | :--- |
| **Cerebras** | `llama-3.3-70b` | Ultra-fast (~2100 tps) | Instant Chat, Executive Summaries |
| **Groq** | `llama-3.3-70b-versatile`, `deepseek-r1-distill-llama-70b` | Fast (~400 tps) | Secondary Streaming & Reasoning |
| **Google Gemini** | `gemini-2.5-flash`, `gemini-2.5-pro` | High Context (1M tokens) | Full Document Context & Synthesis |
| **HuggingFace** | `Qwen/Qwen2.5-Coder-32B-Instruct` | Specialized | Code Extraction & Equation Auditing |
| **OpenRouter** | Free backup models | Variable | Ultimate Resiliency Safety Net |

---

## 8. Master Synthesis: Complete Integrated End-to-End Architecture

### 8.1 The Unified System Blueprint
Now that all 6 divisions are defined, the diagram below maps how every division interacts across process, network, and memory boundaries during live operation.

```mermaid
flowchart TB
    %% Division 1
    subgraph D1["Division 1: Native Desktop Shell (Electron + Win32)"]
        Win32["Win32 Shell (Taskbar FFI)"] <--> MainProcess["Electron Main Process"]
        MainProcess --> MWindow["Mascot Transparent Window"]
        MainProcess --> SWindow["Sidebar Docked Window"]
    end

    %% Division 2
    subgraph D2["Division 2: Mascot Engine (13-State FSM)"]
        MWindow --- FSM["13-State FSM Controller"]
        FSM --> SpriteCanvas["Sprite Sheet Renderer (128x128)"]
        FSM --> AudioEngine["Web Audio Feedback"]
    end

    %% Division 3
    subgraph D3["Division 3: Frontend UI Layer (React 19 + Zustand)"]
        SWindow --- ReactView["React 19 Glassmorphic UI"]
        ReactView <--> ZStores["Zustand Stores (Mascot, Paper, Chat)"]
        SSEClient["SSE Stream Listener"] --> ZStores
    end

    %% Division 4
    subgraph D4["Division 4: Backend Bridge Layer (FastAPI REST & SSE)"]
        FastAPIApp["FastAPI Server (Port 8000)"]
        RunQueue["Async Event Queues (run_id)"]
        FastAPIApp --> RunQueue
    end

    %% Division 5
    subgraph D5["Division 5: LangGraph Pipeline (Document Extraction & Agents)"]
        Extractor["Docling / PyMuPDF Extractor"]
        LGGraph["LangGraph Multi-Node StateGraph"]
        Extractor --> LGGraph
    end

    %% Division 6
    subgraph D6["Division 6: Model Router & Multi-Provider Cascade"]
        RouterEngine["Dual-Tier Model Router"]
        ProviderPool["Cerebras | Groq | Gemini | HuggingFace | OpenRouter"]
        RouterEngine <--> ProviderPool
    end

    %% Cross-Division Connections
    ZStores -->|POST /analyze or /chat| FastAPIApp
    RunQueue -->|SSE Stream Events| SSEClient
    FastAPIApp --> Extractor
    LGGraph <--> RouterEngine
    ZStores -->|mascot:set-state IPC| FSM
```

---

### 8.2 End-to-End Execution Trace: Paper Ingestion Lifecycle

The following sequence trace illustrates how an action propagates through every division:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Electron as [D1] Electron Shell
    participant ReactUI as [D3] React 19 / Zustand
    participant Mascot as [D2] Mascot 13-FSM
    participant FastAPI as [D4] FastAPI Server
    participant LangGraph as [D5] LangGraph Pipeline
    participant Router as [D6] Model Router

    User->>ReactUI: Drops PDF file into Dropzone
    ReactUI->>FastAPI: POST /analyze (multipart PDF)
    FastAPI-->>ReactUI: Return 200 OK + { run_id: "abc-123" }
    
    ReactUI->>FastAPI: Connect GET /stream/abc-123
    ReactUI->>Electron: IPC: mascot:set-state("reading")
    Electron->>Mascot: Trigger "reading" sprite animation
    
    FastAPI->>LangGraph: Initialize StateGraph with PDF
    LangGraph->>LangGraph: Extract text, tables, math (Docling)
    
    LangGraph->>FastAPI: Put Event: step_progress("Extracting sections...")
    FastAPI-->>ReactUI: SSE Event: step_progress
    ReactUI->>ReactUI: Update Progress Bar in Zustand
    
    LangGraph->>Router: Dispatch Executive Summary Prompt
    Router->>Router: Select Cerebras Llama 3.3 70B (Speed Tier)
    Router-->>LangGraph: Stream summary tokens
    
    LangGraph->>FastAPI: Put Event: mascot_state("thinking")
    FastAPI-->>ReactUI: SSE Event: mascot_state
    ReactUI->>Mascot: Trigger "thinking" animation
    
    LangGraph->>Router: Dispatch Deep Technical & Formula Audit
    Router->>Router: Select Gemini 2.5 Pro / Qwen 2.5 Coder
    Router-->>LangGraph: Return structured analysis
    
    LangGraph->>FastAPI: Put Event: result(full_analysis_json)
    FastAPI-->>ReactUI: SSE Event: result
    ReactUI->>ReactUI: Render Tabs (Summary, Math, Deep Dive)
    ReactUI->>Mascot: Trigger "celebrating" animation (5s) -> then "idle"
```

---

### 8.3 Summary Table: Division Interfaces & Protocols

| Interaction Path | Source Division | Target Division | Protocol / Transport | Data Payload |
| :--- | :--- | :--- | :--- | :--- |
| **Native Docking** | Division 1 (Main) | OS Taskbar | Win32 FFI (`koffi`) | `APPBARDATA` struct coordinates |
| **Mascot Sync** | Division 3 (Zustand) | Division 2 (Mascot FSM) | Electron IPC | `mascot:set-state { state: string }` |
| **Pipeline Trigger** | Division 3 (React UI) | Division 4 (FastAPI) | HTTP POST (`/analyze`) | PDF Binary / File Path |
| **Live Streaming** | Division 4 (FastAPI) | Division 3 (SSE Client) | HTTP SSE (`text/event-stream`) | JSON events (`step_progress`, `token`) |
| **Agent Execution** | Division 4 (FastAPI) | Division 5 (LangGraph) | Python Async In-Process | `AgentState` TypedDict |
| **LLM Inference** | Division 5 (LangGraph) | Division 6 (Router) | HTTP REST / OpenAI Client | Prompt, System Message, Model Params |
| **Failover Handshake**| Division 6 (Router) | Provider APIs | HTTP REST with retry | Auth Token, Stream Buffer, Status 429 |
