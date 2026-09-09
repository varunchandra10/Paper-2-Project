"use client";

import React, { useState } from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { 
  Terminal, 
  Copy, 
  Check, 
  Play, 
  Download, 
  Sparkles, 
  Layers, 
  Cpu, 
  ShieldCheck,
  CheckCircle2,
  ExternalLink
} from "lucide-react";

interface CLISectionProps {
  onOpenDownload?: () => void;
}

export function CLISection({ onOpenDownload }: CLISectionProps) {
  const [activeTab, setActiveTab] = useState<"e2e" | "backend" | "electron" | "ollama">("e2e");
  const [copied, setCopied] = useState(false);

  const cliTabs = [
    {
      id: "e2e" as const,
      label: "1. Ingest & Synthesize Paper",
      command: "python backend/test_pipeline_e2e.py --paper papers/sample_papers/[1].pdf",
      description: "Extracts multi-modal sections, runs 8-agent reasoning mesh, and generates verified 8-file PyTorch package.",
      output: [
        "[0.42s] [EXTRACTION] ExtractionRouter -> PyMuPDF + Docling parsing started",
        "[0.88s] [CANONICAL] CanonicalPaperDocument schema generated (Completeness: 1.00)",
        "[1.34s] [RETRIEVAL] FAISS Cosine Index populated (14 semantic chunks indexed)",
        "[2.15s] [AGENTS] DecompositionAgent mapped 4 sub-modules: [Encoder, Decoder, Attention, Loss]",
        "[2.89s] [FEASIBILITY] VRAM Feasibility: Estimated 3.42 GB (Passes host RTX 5050 8GB limit)",
        "[4.50s] [SYNTHESIS] DualCodeEngine dispatched Gemini 2.5 Flash + Qwen 2.5 Coder 32B",
        "[5.80s] [VERIFIER] 3-Layer Virtual AST Gate: ast.parse passed (100% syntax compliance)",
        "[6.10s] [VERIFIER] Security Blacklist: 0 unsafe imports found (os/subprocess blocked)",
        "[6.45s] [VERIFIER] Mock Tensor Runner: forward(x) pass validated [batch=2, hidden=768]",
        "[SUCCESS] 8-File PyTorch Package Synthesized at: backend/output/[1]_LoRA_PyTorch/",
      ],
    },
    {
      id: "backend" as const,
      label: "2. Launch FastAPI Gateway",
      command: "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload",
      description: "Starts local ASGI REST gateway, SSE pipeline event streams, and psutil hardware telemetry poller.",
      output: [
        "INFO:     Will watch for changes in: ['backend/app']",
        "INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)",
        "INFO:     CORS enabled for origins: ['http://localhost:5173', 'app://.']",
        "INFO:     FastAPI Gateway mounted 18 endpoints (/papers, /pipeline, /chat, /stream)",
        "INFO:     SSE EventSource broadcaster initialized for real-time desktop sync",
        "INFO:     Application startup complete. Ready for Electron client interop.",
      ],
    },
    {
      id: "electron" as const,
      label: "3. Launch Win32 Desktop App",
      command: "npm run electron:start",
      description: "Initializes Koffi C-FFI Shell32 taskbar docking and 13-state animated mascot overlay.",
      output: [
        "[Koffi] C-FFI Bound: shell32.dll -> SHAppBarMessage(ABM_GETTASKBARPOS)",
        "[Display] Primary Monitor workArea: { x: 0, y: 0, width: 1920, height: 1040 }",
        "[WindowManager] Snapped mascotWindow (125x150) atop Windows taskbar edge",
        "[WindowManager] Snapped panelWindow (340x480) +18px above mascot head",
        "[MascotEngine] Initialized 60FPS Canvas2D Sprite Engine (State: 'wave')",
        "[IPC] EventSource connected to backend: http://127.0.0.1:8000/stream",
      ],
    },
    {
      id: "ollama" as const,
      label: "4. 100% Local Offline LLM",
      command: "ollama run qwen2.5-coder:32b",
      description: "Run code synthesis entirely on your local GPU with zero cloud API keys and no external network calls.",
      output: [
        "pulling manifest: 100%",
        "verifying sha256 digest: 100%",
        "loading model into VRAM: 18.4 GB allocated",
        "RUEXIS router detected local Ollama provider at http://127.0.0.1:11434",
        "Zero-cloud fallback active: Requests Per Minute (RPM) quota tracking disabled (Unlimited)",
        "Local inference ready for offline literature-to-PyTorch compilation.",
      ],
    },
  ];

  const currentTab = cliTabs.find((t) => t.id === activeTab) || cliTabs[0];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentTab.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="cli" className="py-24 bg-[#18181B] border-t border-white/8 relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 left-1/3 -translate-x-1/2 w-[700px] h-[350px] bg-[#DA7756]/8 rounded-full blur-[150px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[300px] bg-[#38BDF8]/6 rounded-full blur-[140px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading Commented Out
        <SectionHeading
          badge="DEVELOPER CLI & QUICKSTART"
          badgeVariant="accent"
          title="Run RUEXIS Locally"
          highlightText="in Under 60 Seconds"
          description="Synthesize academic research papers into runnable PyTorch packages directly from your terminal, or launch the native Win32 desktop companion."
        />
        */}

        {/* Main Terminal Window Container */}
        <div className="max-w-5xl mx-auto rounded-3xl bg-[#141416] border border-white/10 shadow-2xl overflow-hidden backdrop-blur-xl">
          
          {/* Terminal Window Header Bar */}
          <div className="p-3.5 bg-[#1C1C20] border-b border-white/8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            {/* Traffic Light Dots & Title */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 pl-1">
                <span className="w-3 h-3 rounded-full bg-[#EF4444]" />
                <span className="w-3 h-3 rounded-full bg-[#F59E0B]" />
                <span className="w-3 h-3 rounded-full bg-[#10B981]" />
              </div>
              <span className="text-xs font-mono text-[#9E9E99] flex items-center gap-1.5 border-l border-white/10 pl-3">
                <Terminal className="w-3.5 h-3.5 text-[#DA7756]" />
                <span>bash — ruexis-runtime@local</span>
              </span>
            </div>

            {/* Header Right Action: Download Desktop App Button */}
            {onOpenDownload && (
              <button
                onClick={onOpenDownload}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#DA7756]/15 hover:bg-[#DA7756]/25 border border-[#DA7756]/30 text-xs font-mono text-[#DA7756] font-semibold transition-all cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Desktop Client</span>
              </button>
            )}
          </div>

          {/* CLI Tab Selector Ribbon */}
          <div className="p-2 bg-[#18181B] border-b border-white/8 flex items-center gap-2 overflow-x-auto scrollbar-none">
            {cliTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setCopied(false);
                }}
                className={`py-2 px-3 rounded-xl text-xs font-mono font-medium transition-all shrink-0 cursor-pointer flex items-center gap-2 ${
                  activeTab === tab.id
                    ? "bg-[#222227] text-[#F4F3EE] border border-white/10 shadow-sm font-semibold"
                    : "text-[#71717A] hover:text-[#9E9E99] hover:bg-white/5"
                }`}
              >
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Terminal Command Input Area */}
          <div className="p-4 sm:p-5 bg-[#131315] border-b border-white/5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 font-mono text-xs sm:text-sm text-[#F4F3EE] overflow-x-auto py-1">
              <span className="text-[#DA7756] font-bold select-none">$</span>
              <span className="text-[#38BDF8] select-all">{currentTab.command}</span>
            </div>

            <button
              onClick={handleCopy}
              className="p-2 rounded-xl bg-[#222227] hover:bg-[#2A2A32] border border-white/10 text-[#F4F3EE] transition-colors shrink-0 cursor-pointer"
              title="Copy Command to Clipboard"
            >
              {copied ? (
                <div className="flex items-center gap-1.5 text-xs text-[#34D399] font-mono font-bold px-1">
                  <Check className="w-3.5 h-3.5" />
                  <span>Copied</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-xs text-[#9E9E99] font-mono px-1">
                  <Copy className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Copy</span>
                </div>
              )}
            </button>
          </div>

          {/* Terminal Real Output Console */}
          <div className="p-5 bg-[#0F0F12] font-mono text-xs text-[#D4D4D8] space-y-1.5 max-h-72 overflow-y-auto select-text">
            <div className="text-[11px] text-[#71717A] mb-3 pb-2 border-b border-white/5 flex items-center justify-between">
              <span>{currentTab.description}</span>
              <span className="text-[#34D399] flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Verified Local Pipeline
              </span>
            </div>

            {currentTab.output.map((line, idx) => (
              <div 
                key={idx} 
                className={`leading-relaxed ${
                  line.includes("[SUCCESS]")
                    ? "text-[#34D399] font-bold bg-[#34D399]/10 p-2 rounded-lg border border-[#34D399]/20 my-2"
                    : line.includes("[FEASIBILITY]") || line.includes("VRAM allocated")
                    ? "text-[#A855F7]"
                    : line.includes("[VERIFIER]") || line.includes("100%")
                    ? "text-[#38BDF8]"
                    : line.includes("[Koffi]") || line.includes("[WindowManager]")
                    ? "text-[#EC4899]"
                    : "text-[#9E9E99]"
                }`}
              >
                {line}
              </div>
            ))}
          </div>

          {/* Terminal Footer Bar */}
          <div className="p-3 bg-[#18181B] border-t border-white/8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-[#71717A]">
            <div className="flex items-center gap-4">
              <span>Python 3.11+</span>
              <span>•</span>
              <span>PyTorch 2.2+</span>
              <span>•</span>
              <span>CUDA 12+ / CPU (Windows 11/10)</span>
            </div>

            <a
              href="https://github.com/varunchandra10/Paper-2-Project"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#DA7756] hover:underline flex items-center gap-1"
            >
              <span>View setup instructions on GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

        </div>

      </div>
    </section>
  );
}
