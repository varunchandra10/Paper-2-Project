export interface ProtocolContract {
  interaction: string;
  source: string;
  target: string;
  transport: string;
  payload: string;
  sla: string;
}

export const PROTOCOL_MATRIX: ProtocolContract[] = [
  {
    interaction: "Native Docking & Taskbar Discovery",
    source: "Division 1 (Electron Main)",
    target: "OS Taskbar (Shell_TrayWnd)",
    transport: "Win32 C-FFI (koffi)",
    payload: "APPBARDATA struct coordinates { uEdge, rc }",
    sla: "< 0.2ms query"
  },
  {
    interaction: "Mascot State Synchronization",
    source: "Division 3 (Zustand Stores)",
    target: "Division 2 (Mascot FSM Canvas)",
    transport: "Electron IPC Channel",
    payload: "mascot:set-state { state: string, speech?: string }",
    sla: "< 1ms local IPC"
  },
  {
    interaction: "Research Paper Ingestion Trigger",
    source: "Division 3 (React Dropzone)",
    target: "Division 4 (FastAPI Bridge)",
    transport: "HTTP POST multipart/form-data (/analyze)",
    payload: "PDF binary stream + client metadata",
    sla: "Async 200 OK + run_id"
  },
  {
    interaction: "Real-time Telemetry & Token Streaming",
    source: "Division 4 (FastAPI Bridge)",
    target: "Division 3 (SSE Consumer)",
    transport: "HTTP Server-Sent Events (/stream/{run_id})",
    payload: "JSON { event: 'step_progress' | 'token' | 'result' }",
    sla: "< 25ms chunk delivery"
  },
  {
    interaction: "Agentic StateGraph Execution",
    source: "Division 4 (FastAPI Bridge)",
    target: "Division 5 (LangGraph Pipeline)",
    transport: "Python In-Process Async Task",
    payload: "AgentState TypedDict (chunks, tables, formulas)",
    sla: "Parallel multi-agent"
  },
  {
    interaction: "Inference Mesh Dispatch",
    source: "Division 5 (LangGraph Nodes)",
    target: "Division 6 (Model Router)",
    transport: "Async Engine Client Layer",
    payload: "PromptPayload { tier: 'Speed' | 'Deep', max_tokens }",
    sla: "Auto-failover on 429"
  },
  {
    interaction: "Multi-Provider Dynamic Failover",
    source: "Division 6 (Model Router)",
    target: "Cerebras / Groq / Gemini / HF / OpenRouter",
    transport: "HTTPS REST / OpenAI API Spec",
    payload: "ChatCompletion request with fallback headers",
    sla: "99.99% continuity"
  }
];

export interface FSMState {
  id: string;
  name: string;
  trigger: string;
  frameRate: string;
  behavior: string;
  soundCue: string;
  accentColor: string;
}

export const FSM_STATES: FSMState[] = [
  {
    id: "sleeping",
    name: "Sleeping",
    trigger: "App Startup / Inactivity > 300s",
    frameRate: "8 FPS",
    behavior: "Gentle eye closed breathing loop",
    soundCue: "Silent",
    accentColor: "#71717A"
  },
  {
    id: "waking",
    name: "Waking",
    trigger: "User Clicks Mascot from Sleep",
    frameRate: "12 FPS",
    behavior: "Yawn and stretch transition into idle",
    soundCue: "Soft chime",
    accentColor: "#DA7756"
  },
  {
    id: "idle",
    name: "Idle",
    trigger: "Default active baseline",
    frameRate: "8 FPS",
    behavior: "Subtle breathing and ambient attention",
    soundCue: "Silent",
    accentColor: "#34D399"
  },
  {
    id: "blinking",
    name: "Blinking",
    trigger: "Random timer (3s - 8s)",
    frameRate: "14 FPS",
    behavior: "4-frame natural eye blink",
    soundCue: "Silent",
    accentColor: "#38BDF8"
  },
  {
    id: "waving",
    name: "Waving",
    trigger: "User click / Welcome greeting",
    frameRate: "12 FPS",
    behavior: "Friendly paw wave towards user",
    soundCue: "Micro-chirp",
    accentColor: "#FBBF24"
  },
  {
    id: "reading",
    name: "Reading",
    trigger: "PDF Ingestion Started (/analyze)",
    frameRate: "10 FPS",
    behavior: "Eyes panning back and forth with document icon",
    soundCue: "Paper flip sweep",
    accentColor: "#818CF8"
  },
  {
    id: "thinking",
    name: "Thinking",
    trigger: "LangGraph Parallel Nodes Active",
    frameRate: "12 FPS",
    behavior: "Floating lightbulb with rotating aura",
    soundCue: "Low-frequency hum",
    accentColor: "#FBBF24"
  },
  {
    id: "writing",
    name: "Writing",
    trigger: "Summary / Technical Report Streaming",
    frameRate: "14 FPS",
    behavior: "Rapid quill scribble animation",
    soundCue: "Subtle key clicks",
    accentColor: "#DA7756"
  },
  {
    id: "celebrating",
    name: "Celebrating",
    trigger: "Analysis Complete / Result Ready",
    frameRate: "16 FPS",
    behavior: "Excited jump with confetti particles",
    soundCue: "Triumphant fanfare",
    accentColor: "#34D399"
  },
  {
    id: "tired",
    name: "Tired",
    trigger: "Inactivity > 120s without input",
    frameRate: "8 FPS",
    behavior: "Drooping eyelids and heavy posture",
    soundCue: "Gentle sigh",
    accentColor: "#71717A"
  },
  {
    id: "searching",
    name: "Searching",
    trigger: "Chat Question Dispatched",
    frameRate: "12 FPS",
    behavior: "Looking through magnifying glass with radar pulse",
    soundCue: "Sonar ping",
    accentColor: "#38BDF8"
  },
  {
    id: "talking",
    name: "Talking",
    trigger: "LLM Token Streaming to Drawer",
    frameRate: "14 FPS",
    behavior: "Mouth opening/closing in sync with token cadence",
    soundCue: "Synthesized blips",
    accentColor: "#DA7756"
  },
  {
    id: "error",
    name: "Error",
    trigger: "Backend 500 / All Providers 429",
    frameRate: "10 FPS",
    behavior: "Startled expression with warning triangle",
    soundCue: "Double buzz",
    accentColor: "#EF4444"
  }
];

export interface RouterTier {
  name: string;
  focus: string;
  throughput: string;
  cascade: {
    priority: number;
    provider: string;
    model: string;
    speed: string;
    role: string;
  }[];
}

export const ROUTER_TIERS: RouterTier[] = [
  {
    name: "Speed Tier",
    focus: "Ultra-low latency streaming, interactive chat, and executive summaries",
    throughput: "Up to 2100+ Tokens / Second",
    cascade: [
      { priority: 1, provider: "Cerebras", model: "llama-3.3-70b", speed: "~2100 TPS", role: "Primary Instant Streamer" },
      { priority: 2, provider: "Groq", model: "llama-3.3-70b-versatile", speed: "~400 TPS", role: "High-TPS Rapid Fallback" },
      { priority: 3, provider: "Google Gemini", model: "gemini-2.5-flash", speed: "High Context", role: "Massive Context Backup" },
      { priority: 4, provider: "HuggingFace", model: "Serverless Inference", speed: "Standard", role: "Serverless Reserve" },
      { priority: 5, provider: "OpenRouter", model: "Free Tier Multi-Model", speed: "Variable", role: "Ultimate Continuity Net" }
    ]
  },
  {
    name: "Deep Reasoning Tier",
    focus: "Complex algorithmic breakdown, mathematical proof audits, and code generation",
    throughput: "High Reasoning & 1M+ Context Depth",
    cascade: [
      { priority: 1, provider: "Google Gemini", model: "gemini-2.5-pro", speed: "Deep Reasoning", role: "Primary Mathematical Synthesizer" },
      { priority: 2, provider: "HuggingFace", model: "Qwen/Qwen2.5-Coder-32B", speed: "Specialized Code", role: "Python & KaTeX Verification" },
      { priority: 3, provider: "Groq", model: "deepseek-r1-distill-llama-70b", speed: "Reasoning Chain", role: "Distilled Chain-of-Thought" },
      { priority: 4, provider: "Cerebras", model: "llama-3.3-70b", speed: "~2100 TPS", role: "High-Speed Synthesis Backup" },
      { priority: 5, provider: "OpenRouter", model: "Open Source Frontier", speed: "Variable", role: "Emergency Failover Anchor" }
    ]
  }
];
