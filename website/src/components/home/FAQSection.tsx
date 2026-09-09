"use client";

import React, { useState } from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { 
  ChevronDown, 
  HelpCircle, 
  ShieldCheck, 
  Cpu, 
  FileText, 
  Monitor, 
  Sparkles,
  Layers,
  ArrowRight
} from "lucide-react";

interface FAQItem {
  question: string;
  category: string;
  icon: React.ReactNode;
  answer: string;
  points: string[];
}

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs: FAQItem[] = [
    {
      question: "Can RUEXIS run 100% offline without external cloud API keys?",
      category: "PRIVACY & OFFLINE",
      icon: <Cpu className="w-4 h-4 text-[#38BDF8]" />,
      answer: "Yes. RUEXIS AI was engineered as a local-first platform. When offline mode is enabled, code synthesis runs on local Ollama models (such as qwen2.5-coder:32b and deepseek-r1), semantic RAG retrieval executes against on-disk FAISS indexes, and knowledge graph traversal runs via local NetworkX.",
      points: [
        "Zero telemetry or paper data sent to third-party cloud servers",
        "Sub-millisecond FAISS vector similarity search directly on disk",
        "Zero single-model reliance: plug in self-hosted vLLM, SGLang, or Ollama endpoints with automatic fallback",
        "Cloud models (Google Gemini 2.5 Flash, Groq LPUs) are strictly optional accelerators",
      ],
    },
    {
      question: "How does RUEXIS guarantee 100% AST syntax conformance in PyTorch code?",
      category: "COMPILER VERIFICATION",
      icon: <ShieldCheck className="w-4 h-4 text-[#34D399]" />,
      answer: "Every synthesized file passes through our 3-Layer Virtual AST Gate before being written to disk. The compiler parses the code tree into an Abstract Syntax Tree (ast.parse) to catch syntax errors or invalid indentation, scans for security blacklisted imports, and executes mock tensor forward-passes.",
      points: [
        "Layer 1: Native Python ast.parse audit catching syntax errors and unclosed brackets",
        "Layer 2: AST NodeVisitor security blacklist blocking os.system, subprocess, and sockets",
        "Layer 3: Dummy tensor forward-pass simulation proving tensor dimensions align across layers",
      ],
    },
    {
      question: "How does the desktop companion dock seamlessly to the physical Windows taskbar?",
      category: "WIN32 DESKTOP C-FFI",
      icon: <Monitor className="w-4 h-4 text-[#EC4899]" />,
      answer: "Rather than relying on hacky HTML overlays, RUEXIS binds directly to Windows shell32.dll using koffi (C-level Foreign Function Interface). It invokes the Win32 function SHAppBarMessage(ABM_GETTASKBARPOS) to detect physical taskbar screen coordinates, DPI scaling factors, and screen work areas.",
      points: [
        "Dual-window architecture: 125x150 mascot overlay + 340x480 floating React panel",
        "Lockstep dragging keeps both windows perfectly synchronized across multiple monitors",
        "Transparent canvas mouse pass-through prevents desktop interference during normal work",
      ],
    },
    {
      question: "What paper layouts and scientific document formats are supported?",
      category: "MULTI-MODAL INGESTION",
      icon: <FileText className="w-4 h-4 text-[#DA7756]" />,
      answer: "RUEXIS supports all standard academic PDF publications, including complex multi-column conference papers (arXiv, IEEE, ACM, NeurIPS, CVPR, ICLR). An intelligent ExtractionRouter cascades tasks across three specialized parsing engines for maximum fidelity.",
      points: [
        "PyMuPDF: Sub-850ms geometric layout extraction and bounding box detection",
        "GROBID: Extraction of structured TEI-XML citations, authors, and bibliographic headers",
        "IBM Docling: Multi-column tabular data parsing and dynamic LaTeX formula extraction",
      ],
    },
    {
      question: "How are missing paper hyperparameters and mathematical gaps resolved?",
      category: "AGENTIC REASONING",
      icon: <Layers className="w-4 h-4 text-[#A855F7]" />,
      answer: "Academic papers frequently omit implementation details like weight initialization schemes, learning rate warmup steps, or tensor dimension projections. Our autonomous GapAgent cross-references extracted parameters with canonical deep learning architectures to inject verified defaults.",
      points: [
        "Identifies missing hyperparameters and applies mathematically sound PyTorch defaults",
        "Generates a complete FeasibilityReport documenting every assumed parameter",
        "Simulates GPU VRAM consumption against host hardware limits before code synthesis",
      ],
    },
    {
      question: "What local hardware is required to run RUEXIS on a personal computer?",
      category: "HARDWARE SPECS",
      icon: <Sparkles className="w-4 h-4 text-[#FBBF24]" />,
      answer: "The platform is optimized to run smoothly on modern Windows workstations. Hybrid-cloud mode requires minimal resources (8GB RAM, CPU-only). For full offline mode with local 32B code models, an NVIDIA GPU with 8GB–16GB VRAM (e.g. RTX 3060, 4060, 5050) with CUDA 12+ is recommended.",
      points: [
        "Minimum: 8GB RAM, dual-core CPU (using cloud inference or local 7B models)",
        "Recommended: 16GB+ RAM, NVIDIA RTX GPU with CUDA 12+ support",
        "Windows 11 / 10 64-bit with native Win32 C-FFI Shell32 taskbar integration",
      ],
    },
  ];

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="py-24 bg-[#141416] border-t border-white/8 relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/3 right-1/4 w-[600px] h-[350px] bg-[#DA7756]/8 rounded-full blur-[150px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 left-1/4 w-[500px] h-[300px] bg-[#38BDF8]/6 rounded-full blur-[140px] pointer-events-none -z-10" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading */}
        <SectionHeading
          badge="FREQUENTLY ASKED QUESTIONS"
          badgeVariant="accent"
          title="Everything You Need to Know"
          highlightText="About RUEXIS AI"
          description="Detailed architectural answers regarding offline execution, 3-layer AST code verification, native Win32 docking, and hardware requirements."
        />

        {/* Accordion List */}
        <div className="space-y-4">
          {faqs.map((faq, index) => {
            const isOpen = openIndex === index;

            return (
              <div
                key={faq.question}
                className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                  isOpen
                    ? "bg-[#1C1C20] border-[#DA7756]/40 shadow-[0_0_30px_rgba(218,119,86,0.12)]"
                    : "bg-[#18181B]/90 border-white/8 hover:border-white/15 hover:bg-[#1C1C20]/80"
                }`}
              >
                {/* Accordion Header Button */}
                <button
                  onClick={() => toggleFAQ(index)}
                  className="w-full p-5 sm:p-6 text-left flex items-start sm:items-center justify-between gap-4 cursor-pointer"
                >
                  <div className="flex items-start sm:items-center gap-3.5">
                    <div className="p-2 rounded-xl bg-[#222227] border border-white/8 shrink-0 mt-0.5 sm:mt-0">
                      {faq.icon}
                    </div>
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#9E9E99] block mb-1">
                        {faq.category}
                      </span>
                      <h4 className="text-base sm:text-lg font-bold font-heading text-[#F4F3EE] leading-snug">
                        {faq.question}
                      </h4>
                    </div>
                  </div>

                  <div
                    className={`p-2 rounded-xl bg-[#222227] border border-white/8 text-[#9E9E99] shrink-0 transition-transform duration-200 ${
                      isOpen ? "rotate-180 text-[#DA7756] border-[#DA7756]/30" : ""
                    }`}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>

                {/* Accordion Content Body */}
                {isOpen && (
                  <div className="px-5 pb-6 sm:px-6 pt-1 border-t border-white/5 space-y-4 animate-in fade-in duration-200">
                    <p className="text-sm text-[#D4D4D8] leading-relaxed font-sans">
                      {faq.answer}
                    </p>

                    {/* Key Technical Bullets */}
                    <div className="p-4 rounded-xl bg-[#141416] border border-white/5 space-y-2">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#DA7756] font-bold block">
                        Key Architectural Highlights:
                      </span>
                      {faq.points.map((pt, pIdx) => (
                        <div key={pIdx} className="text-xs font-mono text-[#9E9E99] flex items-start gap-2">
                          <span className="text-[#DA7756] font-bold">›</span>
                          <span className="text-[#F4F3EE]">{pt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
