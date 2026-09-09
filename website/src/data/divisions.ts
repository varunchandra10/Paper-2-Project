export interface Division {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  category: string;
  tech: string[];
  summary: string;
  keyPoints: string[];
  metrics: { label: string; value: string }[];
  routeAnchor: string;
}

export const DIVISIONS: Division[] = [
  {
    id: "division-1",
    number: 1,
    title: "Desktop Shell & Native Win32 Subsystem",
    subtitle: "Hardware-Aligned Taskbar Docking & Borderless Dual Viewports",
    category: "OS Interop & FFI",
    tech: ["Electron", "Koffi (C-FFI)", "Win32 API", "APPBARDATA"],
    summary: "Bypasses standard Chromium window constraints via direct Win32 SHAppBarMessage C-FFI calls to query physical taskbar bounding coordinates and manage dual transparent viewports with zero border overhead.",
    keyPoints: [
      "Native ABM_GETTASKBARPOS polling directly queries Shell_TrayWnd coordinates",
      "Dynamic 12px vertical Mascot Window auto-offset above system taskbars",
      "Collapsible 420px width right-screen docked sidebar with hardware backdrop blur",
      "IPC Main Event Dispatcher routing native mouse, window, and lifecycle channels"
    ],
    metrics: [
      { label: "FFI Overhead", value: "< 0.2ms" },
      { label: "Window Frame", value: "Borderless" },
      { label: "OS Compatibility", value: "Win 10/11" }
    ],
    routeAnchor: "/architecture#division-1"
  },
  {
    id: "division-2",
    number: 2,
    title: "Mascot Sprite Engine & 13-State FSM",
    subtitle: "Deterministic Sprite State Machine & Real-Time Audio Telemetry",
    category: "Interactive Canvas Engine",
    tech: ["HTML5 Canvas", "13-State FSM", "Web Audio API", "Sprite Sheets"],
    summary: "A client-side interactive desktop sprite governed by a strict 13-state deterministic Finite State Machine, dynamically transitioning frames based on streaming token events, user interactions, and inactive timers.",
    keyPoints: [
      "13 deterministic states: sleeping, waking, idle, blinking, waving, reading, thinking, writing, celebrating, tired, searching, talking, error",
      "128×128 viewport with variable frame rate throttling (8 FPS idle to 16 FPS talking)",
      "Web Audio synthesized micro-chirps on interactive wave, state change, and celebrate triggers",
      "Direct reactive synchronization with backend LangGraph execution milestones via SSE"
    ],
    metrics: [
      { label: "FSM States", value: "13 States" },
      { label: "Sprite Resolution", value: "128×128 px" },
      { label: "Frame Rate", value: "8 - 16 FPS" }
    ],
    routeAnchor: "/architecture#division-2"
  },
  {
    id: "division-3",
    number: 3,
    title: "Frontend UI & Zustand State Fabric",
    subtitle: "Real-Time Streaming View Layer & Multi-Store State Synchronization",
    category: "View & Client State",
    tech: ["React 19", "Zustand", "Tailwind CSS", "SSE Consumer"],
    summary: "Modern React 19 interface with modular Zustand stores receiving continuous Server-Sent Event deltas, delivering live markdown rendering, KaTeX equations, and glassmorphic telemetry meters.",
    keyPoints: [
      "Modular state isolation across useMascotStore, usePaperStore, useChatStore, and useSystemStore",
      "Resilient SSE client consuming /stream/{run_id} token deltas and step progress events",
      "Multi-palette theme engine supporting Claude Terracotta, Arctic Sky, and Linear Iris",
      "Optimistic UI updates for prompt submissions and real-time streaming token assembly"
    ],
    metrics: [
      { label: "Stores", value: "4 Modular" },
      { label: "Render Engine", value: "React 19" },
      { label: "Stream Latency", value: "< 25ms" }
    ],
    routeAnchor: "/architecture#division-3"
  },
  {
    id: "division-4",
    number: 4,
    title: "Backend FastAPI Bridge & Service Layer",
    subtitle: "Asynchronous Pipeline Orchestration & Hardware Telemetry Poller",
    category: "Micro-Service Gateway",
    tech: ["FastAPI", "Python 3.11+", "AsyncIO", "psutil"],
    summary: "High-throughput asynchronous FastAPI gateway managing long-running agent workflows, in-memory run session queues, and live hardware telemetry broadcasting.",
    keyPoints: [
      "Asynchronous lifecycle management coordinating POST /analyze and GET /stream/{run_id}",
      "Thread-safe in-memory run queue manager mapping run IDs to individual AsyncQueues",
      "Hardware telemetry poller extracting live CPU, RAM, and GPU VRAM statistics",
      "CORS and process-isolation security boundaries protecting system runtime"
    ],
    metrics: [
      { label: "Throughput", value: "High Async" },
      { label: "Telemetry Poll", value: "1000ms" },
      { label: "Endpoints", value: "REST + SSE" }
    ],
    routeAnchor: "/architecture#division-4"
  },
  {
    id: "division-5",
    number: 5,
    title: "Agentic Ingestion & LangGraph Pipeline",
    subtitle: "5-Node Acyclic StateGraph with Parallel Fan-Out Analysis",
    category: "Agentic Intelligence",
    tech: ["LangGraph", "Docling", "PyMuPDF", "Parallel Fan-Out"],
    summary: "Orchestrates research paper decomposition through an acyclic 5-node LangGraph StateGraph, parsing structural layout and fanning out simultaneously into executive, technical, and mathematical audit agents.",
    keyPoints: [
      "Multi-modal ingestion utilizing IBM Docling with PyMuPDF and OCR failover",
      "Semantic section splitting into abstract, methodology, math formulas, and findings",
      "Parallel analytical fan-out: Executive Summary, Deep Technical Extraction, and Formula Verification",
      "Consolidation and critique node reconciling divergent agent findings into a structured report"
    ],
    metrics: [
      { label: "Graph Nodes", value: "5 Pipeline" },
      { label: "Agents", value: "10 Autonomous" },
      { label: "Fan-Out", value: "3x Parallel" }
    ],
    routeAnchor: "/architecture#division-5"
  },
  {
    id: "division-6",
    number: 6,
    title: "Intelligent Model Router & Fallback Cascade",
    subtitle: "Dual-Tier Cost-Latency Mesh with Autonomous Rate-Limit Failover",
    category: "Inference Mesh",
    tech: ["Cerebras", "Groq", "Google Gemini", "HuggingFace", "OpenRouter"],
    summary: "Self-healing dual-tier LLM inference router coordinating 5 providers. Distributes prompts based on latency and reasoning depth while intercepting HTTP 429 errors for seamless zero-downtime fallback.",
    keyPoints: [
      "Speed Tier prioritizing ultra-high throughput (~2100 TPS via Cerebras Llama 3.3 70B)",
      "Deep Reasoning Tier routing to high-context engines (Gemini 2.5 Pro, Qwen 2.5 Coder 32B)",
      "Autonomous 5-provider fallback cascade with rate-limit and quota exhaustion interception",
      "Live quota tracking preventing threshold violations before requests hit upstream APIs"
    ],
    metrics: [
      { label: "Peak TPS", value: "2100+ TPS" },
      { label: "Providers", value: "5 Cascaded" },
      { label: "Failover SLA", value: "Zero Downtime" }
    ],
    routeAnchor: "/architecture#division-6"
  }
];
