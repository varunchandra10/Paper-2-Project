"use client";

import React from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { Badge } from "../ui/Badge";
import { 
  FileText, 
  Cpu, 
  ShieldCheck, 
  Network, 
  Terminal, 
  Monitor, 
  CheckCircle2, 
  Zap, 
  ArrowUpRight,
  Database,
  Layers,
  Sparkles,
  Workflow
} from "lucide-react";

export function FeaturesSection() {
  const metrics = [
    {
      value: "48 / 48",
      label: "Scientific Papers Ingested",
      badge: "100% Pass Rate",
      badgeVariant: "green" as const,
      description: "End-to-end multi-agent verification across 48 complex deep learning architectures.",
    },
    {
      value: "332 Files",
      label: "PyTorch Packages Synthesized",
      badge: "~24,000+ LOC",
      badgeVariant: "amber" as const,
      description: "Full multi-file repositories complete with models, loss functions, datasets, and training loops.",
    },
    {
      value: "100%",
      label: "AST Syntax Conformance",
      badge: "0 Parse Errors",
      badgeVariant: "cyan" as const,
      description: "Automated Python ast.parse syntax verification and security sandboxing on every generated file.",
    },
    {
      value: "100% Local",
      label: "Zero Cloud API Lock-in",
      badge: "Offline Capable",
      badgeVariant: "purple" as const,
      description: "Local Ollama qwen2.5-coder runtime completely eliminates cloud quotas and HTTP 429 failures.",
    },
  ];

  const features = [
    {
      id: "ingestion",
      subsystem: "EXTRACTION ENGINE",
      title: "Tri-Engine Multi-Modal Paper Ingestion",
      icon: <FileText className="w-5 h-5 text-[#DA7756]" />,
      accentColor: "#DA7756",
      chips: ["PyMuPDF", "GROBID TEI XML", "Docling", "Section Hierarchy Merger"],
      description:
        "High-fidelity paper extraction cascading through coordinate-level geometry, academic XML schemas, and deep visual layout segmentation.",
      highlights: [
        "Coordinate extraction preserves physical PDF layout and equation bounding boxes",
        "GROBID TEI XML resolves IEEE/ACM titles, author trees, abstracts, and citations",
        "Multi-parser reconciliation engine merges text, math, and tables into a unified CanonicalPaperDocument",
      ],
    },
    {
      id: "reasoning",
      subsystem: "AGENTIC ORCHESTRATION",
      title: "Specialized 8-Agent Autonomous Reasoning Mesh",
      icon: <Cpu className="w-5 h-5 text-[#38BDF8]" />,
      accentColor: "#38BDF8",
      chips: ["Decomposition", "Parameter Mining", "VRAM Feasibility", "DAG Sequencing"],
      description:
        "A modular assembly of 8 specialized autonomous agents dissecting research literature into actionable engineering artifacts.",
      highlights: [
        "Decomposition Agent constructs modular ComponentGraph dependency trees",
        "Parameter Agent extracts learning rates, batch sizes, optimizers, and backbones",
        "Feasibility & Gap Agents audit GPU VRAM requirements and resolve unstated paper defaults",
      ],
    },
    {
      id: "verification",
      subsystem: "SYNTHESIS & VALIDATION",
      title: "3-Layer Virtual Code Verification Gate",
      icon: <ShieldCheck className="w-5 h-5 text-[#34D399]" />,
      accentColor: "#34D399",
      chips: ["ast.parse", "Import Sandboxing", "Mock Tensor Execution"],
      description:
        "Every generated line of PyTorch is subjected to rigorous static and dynamic audits prior to export or execution.",
      highlights: [
        "Layer 1: Python AST syntax parser guarantees zero indentation or syntax bugs",
        "Layer 2: Dangerous import blacklist blocks unauthorized subprocess, OS, or socket calls",
        "Layer 3: Mock tensor dimension validation simulates forward-pass layer compatibility",
      ],
    },
    {
      id: "retrieval",
      subsystem: "MEMORY & RETRIEVAL",
      title: "Local Flat-File RAG & Bipartite Knowledge Graph",
      icon: <Network className="w-5 h-5 text-[#A855F7]" />,
      accentColor: "#A855F7",
      chips: ["Semantic Chunker", "Flat-File Vector DB", "NetworkX Graph"],
      description:
        "Self-contained semantic retrieval and graph reasoning operating completely on-disk without external cloud database dependencies.",
      highlights: [
        "Semantic section chunker preserves mathematical formulas and algorithmic blocks",
        "High-speed cosine similarity vector index runs locally with zero API latency",
        "NetworkX bipartite graph maps Models, Datasets, Losses, and Metrics with relational edges",
      ],
    },
    {
      id: "react",
      subsystem: "COGNITIVE LOOP",
      title: "Conversational ReACT Agent with 7 Specialized Tools",
      icon: <Terminal className="w-5 h-5 text-[#F59E0B]" />,
      accentColor: "#F59E0B",
      chips: ["Thought-Action-Observation", "7 Tool Ecosystem", "Episodic Memory"],
      description:
        "Interactive academic reasoning loop providing transparent step-by-step audit trails and multi-turn paper context memory.",
      highlights: [
        "Live ReACT steps accordion reveals Thought → Action → Observation cycles in real time",
        "7 Tools: canonical document inspector, hyperparameter editor, vector search, graph search, memory, and arXiv/scholar search",
        "Interactive parameter configuration lets researchers fine-tune hyperparameters before code synthesis",
      ],
    },
    {
      id: "native",
      subsystem: "NATIVE OS INTEROP",
      title: "Win32 C-FFI Taskbar Docking & Desktop Mascot",
      icon: <Monitor className="w-5 h-5 text-[#EC4899]" />,
      accentColor: "#EC4899",
      chips: ["Koffi C-FFI", "Shell_TrayWnd", "Lockstep Dragging", "13-State FSM"],
      description:
        "Native Windows desktop integration binding directly to Windows shell APIs to anchor an interactive desktop companion.",
      highlights: [
        "Koffi C-FFI calls SHAppBarMessage(ABM_GETTASKBARPOS) to track physical taskbar coordinates",
        "Dual-window lockstep dragging synchronizes transparent mascot overlay with floating React panel",
        "60FPS 2D Canvas sprite engine animates 4 distinct character avatars across 13 emotional states",
      ],
    },
  ];

  return (
    <section id="features" className="py-24 bg-[#18181B] border-t border-white/8 relative overflow-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-[#DA7756]/8 rounded-full blur-[140px] pointer-events-none -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[300px] bg-[#38BDF8]/6 rounded-full blur-[130px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading */}
        <SectionHeading
          badge="SYSTEM CAPABILITIES & BENCHMARKS"
          badgeVariant="accent"
          title="Engineered for Autonomous"
          highlightText="Paper-to-Code Synthesis"
          description="Built from the ground up for deep learning researchers and engineers. Combines multi-modal document extraction, 8 specialized autonomous agents, 3-layer AST code verification, and native Win32 desktop interop."
        />

        {/* 4 Metric Counter Cards (Ribbon) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-16">
          {metrics.map((m) => (
            <div
              key={m.label}
              className="p-6 rounded-2xl bg-[#222227]/90 border border-white/10 hover:border-[#DA7756]/40 transition-all duration-300 shadow-xl relative overflow-hidden group hover:scale-[1.02]"
            >
              {/* Subtle card glow */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full blur-2xl pointer-events-none group-hover:bg-[#DA7756]/15 transition-colors" />

              <div className="flex items-center justify-between mb-3">
                <Badge variant={m.badgeVariant} size="sm">
                  {m.badge}
                </Badge>
                <span className="text-[10px] font-mono text-[#71717A] uppercase tracking-wider">
                  VERIFIED
                </span>
              </div>

              <div className="text-3xl sm:text-4xl font-black font-heading text-[#F4F3EE] tracking-tight group-hover:text-[#DA7756] transition-colors">
                {m.value}
              </div>

              <div className="text-sm font-bold text-[#F4F3EE] font-heading mt-1">
                {m.label}
              </div>

              <p className="text-xs text-[#9E9E99] leading-relaxed mt-2 font-sans">
                {m.description}
              </p>
            </div>
          ))}
        </div>

        {/* Section Subtitle for Feature Grid */}
        <div className="flex items-center justify-between pb-3 mb-8 border-b border-white/8">
          <div className="flex items-center gap-2.5">
            <Workflow className="w-4 h-4 text-[#DA7756]" />
            <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-[#F4F3EE]">
              Core Architectural Capabilities
            </h3>
          </div>
          <span className="text-xs font-mono text-[#9E9E99]">
            6 Core Pillars • Local-First Architecture
          </span>
        </div>

        {/* 6 Core Feature Cards (3x2 Grid) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
          {features.map((feature) => (
            <div
              key={feature.id}
              className="p-6 rounded-2xl bg-[#222227]/80 border border-white/10 hover:border-white/20 transition-all duration-300 flex flex-col justify-between shadow-xl group hover:scale-[1.01]"
            >
              <div>
                {/* Top Row: Icon & Subsystem */}
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-[#18181B] border border-white/10 flex items-center justify-center group-hover:border-white/25 transition-all shadow-inner">
                    {feature.icon}
                  </div>
                  <span className="text-[10px] font-mono text-[#9E9E99] uppercase tracking-wider font-semibold">
                    {feature.subsystem}
                  </span>
                </div>

                {/* Feature Title */}
                <h4 className="text-lg font-bold font-heading text-[#F4F3EE] mb-2.5 group-hover:text-[#DA7756] transition-colors">
                  {feature.title}
                </h4>

                {/* Description */}
                <p className="text-xs text-[#9E9E99] leading-relaxed mb-4 font-sans">
                  {feature.description}
                </p>

                {/* Technical Highlights */}
                <ul className="space-y-2 mb-6">
                  {feature.highlights.map((h, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-[#D4D4D8] font-sans leading-relaxed">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#34D399] shrink-0 mt-0.5" />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Bottom Chip Badges */}
              <div className="pt-4 border-t border-white/8 flex flex-wrap gap-1.5">
                {feature.chips.map((chip) => (
                  <span
                    key={chip}
                    className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#18181B] border border-white/10 text-[#9E9E99]"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
