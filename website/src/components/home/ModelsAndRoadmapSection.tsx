"use client";

import React, { useState } from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { 
  Cpu, 
  Sparkles, 
  Workflow, 
  ShieldCheck, 
  Layers, 
  Zap, 
  CheckCircle2, 
  Clock, 
  Rocket, 
  ArrowRight,
  Database,
  Terminal,
  Activity,
  GitBranch
} from "lucide-react";

export function ModelsAndRoadmapSection() {
  const [activeTab, setActiveTab] = useState<"models" | "roadmap">("models");

  const modelTiers = [
    {
      id: "gemini",
      name: "Google Gemini 2.5 Flash",
      tier: "LONG-CONTEXT REASONING TIER",
      role: "Mathematical Derivations & Full-Paper Synthesis",
      context: "1,000,000 Tokens",
      speed: "Fast (~140 TPS)",
      color: "#DA7756",
      tag: "Cloud / Google GenAI",
      details: "Operates across the full paper context to analyze theorems, extract LaTeX equations, resolve architectural dependencies, and generate structured DAG specifications.",
      specs: ["1M Context Window", "Multimodal Equation Parsing", "Dedicated Backend Key"],
    },
    {
      id: "qwen",
      name: "Qwen 2.5 Coder 32B Instruct",
      tier: "IDIOMATIC PYTORCH SYNTHESIS TIER",
      role: "Modular Deep Learning Code Generation",
      context: "32,768 Tokens",
      speed: "High-Throughput",
      color: "#38BDF8",
      tag: "Hugging Face / Local Ollama",
      details: "Specialized open-weights coding LLM synthesizing clean, PEP-8 compliant PyTorch code with explicit tensor shapes, type hints, docstrings, and nn.Module hierarchies.",
      specs: ["32B Parameters", "PyTorch 2.0+ Idioms", "Runs on RTX 4090 / 5050 / Ollama"],
    },
    {
      id: "deepseek",
      name: "DeepSeek-R1 (Reasoning)",
      tier: "CHAIN-OF-THOUGHT DERIVATION TIER",
      role: "Mathematical Proofs & Hyperparameter Gap Resolution",
      context: "64,000 Tokens",
      speed: "Deep Chain-of-Thought",
      color: "#A855F7",
      tag: "OpenRouter / Local",
      details: "Generates long-form reasoning trajectories to solve unstated paper hyperparameters (learning rates, tensor projections) and optimize mathematical loss functions.",
      specs: ["Chain-of-Thought R1", "Automated Gap Audit", "Zero-Assumption Reasoning"],
    },
    {
      id: "groq",
      name: "Groq LPU Inference Gateway",
      tier: "SUB-SECOND CONVERSATIONAL TIER",
      role: "Multi-Turn ReACT Chat & Live Tool Execution",
      context: "8,192 Tokens",
      speed: "Ultra-Fast (~850+ TPS)",
      color: "#34D399",
      tag: "Groq LPU Hardware",
      details: "Powers real-time conversational Q&A over paper contents, providing instantaneous streaming responses and executing the 7 ReACT academic retrieval tools.",
      specs: ["850+ Tokens/Sec", "Sub-100ms TTFT", "7 ReACT Tool Handlers"],
    },
    {
      id: "ollama",
      name: "Local Ollama 100% Offline Mesh",
      tier: "ZERO-CLOUD SOVEREIGNTY TIER",
      role: "Air-Gapped Local Inference & On-Disk RAG",
      context: "32,768 Tokens",
      speed: "Local GPU Dependent",
      color: "#FBBF24",
      tag: "100% Offline / Local VRAM",
      details: "Enables researchers to analyze proprietary or confidential preprints completely offline with zero data leaving the physical workstation.",
      specs: ["Zero Cloud Calls", "Unlimited Local Quotas", "On-Disk FAISS Retrieval"],
    },
  ];

  const roadmapPhases = [
    {
      phase: "PHASE 01",
      status: "COMPLETED",
      statusColor: "#34D399",
      title: "Core Foundation & 48-Paper Validation",
      subtitle: "Empirical Multi-Agent Engine & Win32 Interop",
      items: [
        "Tri-parser extraction router (PyMuPDF, GROBID, IBM Docling)",
        "LangGraph 5-node autonomous pipeline with 8 domain agents",
        "Dual Code Engine (Gemini 2.5 Flash + Qwen 2.5 Coder 32B)",
        "3-Layer Virtual AST Verifier with 100% syntax compliance",
        "Win32 C-FFI Shell32 taskbar docking & 13-state mascot FSM",
        "48 / 48 research papers synthesized into 332 verified PyTorch files",
      ],
    },
    {
      phase: "PHASE 02",
      status: "CURRENTLY IN PROGRESS",
      statusColor: "#DA7756",
      title: "Active Fine-Tuning & Pipeline Horizons",
      subtitle: "Extensive Ongoing Engineering: Dozens of Capabilities in Active Build",
      items: [
        "Iterative Model Fine-Tuning: Ongoing LoRA & weight refinement trained on newest SOTA academic preprints",
        "Cross-Architecture Synthesis: Fusing transformer, state-space (Mamba), and diffusion modules into unified codebases",
        "Automated Unit Test & Profiling Generation: Auto-synthesizing pytest test suites and tensor memory benchmarks per paper",
        "Rapid Capability Expansions: Many more experimental agents, compiler passes, and visual debugging tools actively underway",
        "Continuous Rollout: Iterative updates rolling out as model checkpoints complete training and verification",
      ],
    },
    {
      phase: "PHASE 03",
      status: "FUTURE MILESTONE",
      statusColor: "#38BDF8",
      title: "Distributed Training & Self-Hosted vLLM Infrastructure",
      subtitle: "Eliminating Single-Model Reliance via Private Model Clusters",
      items: [
        "Self-Hosted Model Runtime: native vLLM & SGLang orchestration eliminating single-provider cloud reliance",
        "Multi-Model Private Mesh: concurrent local routing across self-hosted Qwen, DeepSeek-R1, and Llama nodes",
        "Automated torchrun distributed multi-GPU training script generation",
        "Synthetic and real benchmark dataset loaders (ImageNet, SQuAD, GLUE, arXiv)",
        "Live loss curve telemetry streaming directly to the desktop control panel",
        "Weights & Biases (WandB) and TensorBoard automatic experiment tracking",
      ],
    },
    {
      phase: "PHASE 04",
      status: "FUTURE RESEARCH",
      statusColor: "#A855F7",
      title: "Sovereign In-House Models & Compiler Feedback (RLCF)",
      subtitle: "Autonomous Self-Hosted Weights & Custom CUDA Kernels",
      items: [
        "In-House Model Fine-Tuning: training domain-specific Paper-to-Code weights from 332+ verified AST trees",
        "100% Air-Gapped Private Cloud: enterprise self-hosting with zero external network egress or API dependencies",
        "Triton and CUDA C++ kernel synthesis for custom paper attention mechanisms",
        "Automated FLOPs profiler, AWQ/GGUF quantization, and VRAM scaling optimization loops",
        "Multi-paper comparative synthesis running entirely on self-hosted multi-GPU clusters",
      ],
    },
  ];

  return (
    <section id="models-roadmap" className="py-24 bg-[#141416] border-t border-white/8 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/3 -translate-x-1/2 w-[700px] h-[350px] bg-[#DA7756]/8 rounded-full blur-[160px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-[600px] h-[350px] bg-[#38BDF8]/6 rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading */}
        <SectionHeading
          badge="INTELLIGENCE MESH & ROADMAP"
          badgeVariant="accent"
          title="Multi-Model Ecosystem"
          highlightText="& Future Horizons"
          description="A multi-tier mesh orchestrating specialized LLMs with self-hosted private cluster support to eliminate single-model vendor lock-in, alongside our engineering roadmap."
        />

        {/* View Switcher Tabs */}
        <div className="flex items-center justify-center mb-10">
          <div className="bg-[#1C1C20] p-1.5 rounded-2xl border border-white/10 flex items-center gap-2 shadow-xl">
            <button
              onClick={() => setActiveTab("models")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer ${
                activeTab === "models"
                  ? "bg-[#DA7756] text-white shadow-[0_0_18px_rgba(218,119,86,0.4)]"
                  : "text-[#9E9E99] hover:text-[#F4F3EE]"
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Model Mesh & Providers ({modelTiers.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("roadmap")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer ${
                activeTab === "roadmap"
                  ? "bg-[#38BDF8] text-white shadow-[0_0_18px_rgba(56,189,248,0.4)]"
                  : "text-[#9E9E99] hover:text-[#F4F3EE]"
              }`}
            >
              <Rocket className="w-4 h-4" />
              <span>Future Works & Roadmap</span>
            </button>
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            TAB 1: MULTI-MODEL ECOSYSTEM & PROVIDER MESH
        ───────────────────────────────────────────────────────────── */}
        {activeTab === "models" && (
          <div className="space-y-4 animate-in fade-in duration-300">
            {/* Failover Cascade Banner */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[#1C1C20] border border-white/10 mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-[#DA7756]/15 border border-[#DA7756]/30 text-[#DA7756] shrink-0">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold font-heading text-[#F4F3EE]">
                    Intelligent Model Router & Zero-Downtime Cascade
                  </h4>
                  <p className="text-xs text-[#9E9E99] mt-0.5">
                    An automated sliding-window rate limiter monitors RPM/TPM across external APIs and self-hosted local vLLM/Ollama clusters—cascading automatically to eliminate reliance on any single model provider.
                  </p>
                </div>
              </div>

              <span className="text-[11px] font-mono text-[#34D399] bg-[#34D399]/10 px-3 py-1 rounded-full border border-[#34D399]/20 font-semibold shrink-0">
                Automatic Failover Active
              </span>
            </div>

            {/* Model Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {modelTiers.map((model) => (
                <div
                  key={model.id}
                  className="rounded-2xl bg-[#18181B] border border-white/8 p-5 sm:p-6 flex flex-col justify-between hover:border-white/20 hover:scale-[1.01] transition-all duration-200 shadow-xl relative group overflow-hidden"
                >
                  {/* Ambient top glow */}
                  <div 
                    className="absolute -top-16 left-1/2 -translate-x-1/2 w-40 h-32 rounded-full blur-3xl pointer-events-none opacity-20 group-hover:opacity-40 transition-opacity"
                    style={{ backgroundColor: model.color }}
                  />

                  <div>
                    {/* Top Tier Tag */}
                    <div className="flex items-center justify-between text-[10px] font-mono mb-3">
                      <span 
                        className="font-bold px-2 py-0.5 rounded uppercase tracking-wider"
                        style={{ 
                          backgroundColor: `${model.color}15`, 
                          color: model.color 
                        }}
                      >
                        {model.tier}
                      </span>
                      <span className="text-[#71717A] text-[9px]">{model.speed}</span>
                    </div>

                    {/* Model Name & Role */}
                    <h4 className="text-lg font-bold font-heading text-[#F4F3EE] group-hover:text-[#DA7756] transition-colors leading-tight mb-1">
                      {model.name}
                    </h4>
                    <p className="text-xs font-mono text-[#38BDF8] mb-3">
                      {model.role}
                    </p>

                    {/* Description */}
                    <p className="text-xs text-[#D4D4D8] leading-relaxed mb-4 font-sans">
                      {model.details}
                    </p>
                  </div>

                  {/* Specs & Hardware Chips */}
                  <div className="pt-3 border-t border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-[#71717A]">Context Window:</span>
                      <span className="text-[#F4F3EE] font-bold">{model.context}</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {model.specs.map((spec, i) => (
                        <span 
                          key={i} 
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#222227] border border-white/5 text-[#9E9E99]"
                        >
                          {spec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB 2: FUTURE WORKS & ENGINEERING ROADMAP
        ───────────────────────────────────────────────────────────── */}
        {activeTab === "roadmap" && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
              {roadmapPhases.map((phase, idx) => (
                <div
                  key={phase.phase}
                  className="rounded-2xl bg-[#18181B] border border-white/8 p-5 sm:p-6 flex flex-col justify-between shadow-xl relative overflow-hidden group hover:border-white/20 transition-all"
                >
                  {/* Ambient Top Glow */}
                  <div 
                    className="absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-24 rounded-full blur-2xl pointer-events-none opacity-20 group-hover:opacity-40 transition-opacity"
                    style={{ backgroundColor: phase.statusColor }}
                  />

                  <div>
                    {/* Phase & Status Badge */}
                    <div className="flex items-center justify-between text-xs font-mono mb-3">
                      <span className="font-bold text-[#F4F3EE] tracking-wider">
                        {phase.phase}
                      </span>
                      <span 
                        className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full border truncate max-w-[150px]"
                        style={{
                          backgroundColor: `${phase.statusColor}15`,
                          borderColor: `${phase.statusColor}30`,
                          color: phase.statusColor,
                        }}
                      >
                        {phase.status}
                      </span>
                    </div>

                    {/* Title & Subtitle */}
                    <h4 className="text-lg font-bold font-heading text-[#F4F3EE] leading-snug mb-1">
                      {phase.title}
                    </h4>
                    <p className="text-xs font-mono text-[#9E9E99] mb-4 line-clamp-2">
                      {phase.subtitle}
                    </p>

                    {/* Milestone Checklist */}
                    <div className="space-y-2">
                      {phase.items.map((item, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-[#D4D4D8]">
                          <span 
                            className="mt-0.5 shrink-0 font-bold"
                            style={{ color: phase.statusColor }}
                          >
                            {phase.status === "COMPLETED" ? "✓" : "›"}
                          </span>
                          <span className="leading-relaxed text-[11px]">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Bottom Card Border Accent */}
                  <div 
                    className="mt-6 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-[#71717A]"
                  >
                    <span>Milestone 0{idx + 1}</span>
                    <span style={{ color: phase.statusColor }}>
                      {phase.status === "COMPLETED" 
                        ? "Verified in Prod" 
                        : phase.status === "CURRENTLY IN PROGRESS" 
                        ? "In Active Dev" 
                        : "Future Horizon"}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Continuous Development Notice Callout */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[#1C1C20] border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-[#A855F7]/15 border border-[#A855F7]/30 text-[#A855F7] shrink-0">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold font-heading text-[#F4F3EE] flex items-center gap-2">
                    <span>Active Engineering & Continuous Model Fine-Tuning</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#A855F7]/20 text-[#C084FC] border border-[#A855F7]/30">
                      MANY MORE CAPABILITIES IN PIPELINE
                    </span>
                  </h4>
                  <p className="text-xs text-[#9E9E99] mt-0.5">
                    Extensive active development is underway—fine-tuning specialized model checkpoints, refining autonomous AST verification passes, and engineering dozens more experimental research capabilities to be rolled out continuously.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </section>
  );
}
