export interface AgentSpec {
  id: string;
  name: string;
  role: string;
  tier: "Speed" | "Deep" | "Extraction";
  primaryModel: string;
  fallbackModel: string;
  description: string;
  inputs: string[];
  outputs: string[];
  badgeColor: string;
}

export const SPECIALIZED_AGENTS: AgentSpec[] = [
  {
    id: "agent-ingestion",
    name: "Ingestion Agent",
    role: "Document Layout & Extraction",
    tier: "Extraction",
    primaryModel: "IBM Docling / PyMuPDF OCR",
    fallbackModel: "Tesseract OCR / PDFPlumber",
    description: "Parses complex multi-column academic PDFs, preserving structural table hierarchies, figure captions, and formula bounding boxes.",
    inputs: ["Raw PDF binary / path", "Ingestion parameters"],
    outputs: ["Section-segmented Markdown", "Extracted Tables JSON", "Raw LaTeX Equations"],
    badgeColor: "#38BDF8"
  },
  {
    id: "agent-chunking",
    name: "Semantic Chunking Agent",
    role: "Section Classification & Boundary Detection",
    tier: "Extraction",
    primaryModel: "Regex Heuristics + Groq Llama 3.3 8B",
    fallbackModel: "Local Rule-based Token Splitter",
    description: "Segments academic documents into contextual blocks: Abstract, Methodology, Theoretical Proofs, Experimental Results, and Citations.",
    inputs: ["Segmented Markdown"],
    outputs: ["Semantic Chunks with Token Budgets", "Cross-Reference Map"],
    badgeColor: "#818CF8"
  },
  {
    id: "agent-structure",
    name: "Structure Verification Agent",
    role: "Schema & Hierarchy Validation",
    tier: "Speed",
    primaryModel: "Cerebras Llama 3.3 70B",
    fallbackModel: "Groq Llama 3.3 70B",
    description: "Validates schema compliance and ensures all prerequisite sections exist before triggering the parallel analytical branch.",
    inputs: ["Semantic Chunks"],
    outputs: ["Validated AgentState TypedDict", "Missing Section Flags"],
    badgeColor: "#34D399"
  },
  {
    id: "agent-summary",
    name: "Executive Summary Agent",
    role: "Rapid Synthesis & High-Level Distillation",
    tier: "Speed",
    primaryModel: "Cerebras Llama 3.3 70B (~2100 TPS)",
    fallbackModel: "Groq Llama 3.3 70B-versatile",
    description: "Executes ultra-high-speed synthesis delivering executive takeaways, core novelty assertions, and practical research significance in sub-second time.",
    inputs: ["Abstract", "Introduction", "Conclusion Chunks"],
    outputs: ["Executive TL;DR", "Key Contributions List", "Research Impact Score"],
    badgeColor: "#DA7756"
  },
  {
    id: "agent-technical",
    name: "Deep Technical Agent",
    role: "Methodological & Algorithmic Deconstruction",
    tier: "Deep",
    primaryModel: "Google Gemini 2.5 Pro",
    fallbackModel: "Groq DeepSeek R1 Distill",
    description: "Unpacks mathematical definitions, neural network architectures, ablation studies, and baseline comparative datasets with meticulous analytical rigor.",
    inputs: ["Methodology Chunks", "Table Payloads", "Ablation Data"],
    outputs: ["Algorithmic Breakdown", "Ablation Audit", "Architectural Limitations"],
    badgeColor: "#FBBF24"
  },
  {
    id: "agent-codegen",
    name: "Formula & Code Verification Agent",
    role: "Code Reconstruction & Equation Auditing",
    tier: "Deep",
    primaryModel: "HuggingFace Qwen 2.5 Coder 32B",
    fallbackModel: "Gemini 2.5 Flash",
    description: "Translates abstract mathematical formulas and pseudocode into verified, runnable Python/PyTorch implementations with syntax checks.",
    inputs: ["Raw LaTeX Equations", "Pseudocode Blocks"],
    outputs: ["Executable Python Modules", "KaTeX Equation Explanations", "Shape Audit"],
    badgeColor: "#34D399"
  },
  {
    id: "agent-synthesis",
    name: "Synthesis & Critique Agent",
    role: "Cross-Agent Consensus & Contradiction Resolution",
    tier: "Deep",
    primaryModel: "Google Gemini 2.5 Flash / Pro",
    fallbackModel: "Cerebras Llama 3.3 70B",
    description: "Consolidates parallel outputs from Summary, Deep Tech, and Code Gen agents, eliminating redundancy and highlighting methodological discrepancies.",
    inputs: ["Summary Output", "Tech Breakdown", "Code Artifacts"],
    outputs: ["Unified Research Report", "Critical Weakness Evaluation", "Implementation Feasibility"],
    badgeColor: "#DA7756"
  },
  {
    id: "agent-chat",
    name: "Context-Aware Chat Agent",
    role: "Interactive Multi-Turn Paper Consultation",
    tier: "Speed",
    primaryModel: "Cerebras Llama 3.3 70B",
    fallbackModel: "Groq Llama 3.3 70B",
    description: "Answers precise user queries against the ingested paper, leveraging in-memory contextual embeddings and extracted vector chunks.",
    inputs: ["User Chat Prompt", "Target Paper Chunks", "Conversation History"],
    outputs: ["Token Delta Stream", "Citations with Section Anchors"],
    badgeColor: "#38BDF8"
  },
  {
    id: "agent-model-router",
    name: "Intelligent Model Router Agent",
    role: "Telemetry & Dynamic Inference Orchestration",
    tier: "Speed",
    primaryModel: "Autonomous In-Memory Routing Engine",
    fallbackModel: "Static Fallback Array",
    description: "Monitors quota consumption, token budgets, and status codes in real time, routing queries to the lowest-latency capable model tier.",
    inputs: ["Task Prompt", "Complexity Classifier", "Quota Telemetry"],
    outputs: ["Selected Provider Request", "Live Quota Delta", "Active Fallback Path"],
    badgeColor: "#818CF8"
  },
  {
    id: "agent-mascot-fsm",
    name: "Mascot Telemetry & State Agent",
    role: "Human-System Empathy & Visual Status Engine",
    tier: "Speed",
    primaryModel: "Deterministic State Dispatcher",
    fallbackModel: "Idle Timer Watchdog",
    description: "Translates background pipeline events into synchronized 13-state mascot animations and synthesized audio feedback.",
    inputs: ["LangGraph Node Transitions", "SSE Stream States", "Mouse Gestures"],
    outputs: ["mascot:set-state IPC Payloads", "Web Audio Waveforms", "Speech Bubble Deltas"],
    badgeColor: "#DA7756"
  }
];
