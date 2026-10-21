"use client";

import React, { useState } from "react";
import { Container } from "../layout/Container";
import { 
  Play, 
  ArrowRight, 
  FileText, 
  Code2, 
  CheckCircle2, 
  Cpu, 
  Layers, 
  Sparkles,
  Terminal,
  ExternalLink
} from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";
import { project } from "@/data/project";

export function HeroSection() {
  const [activeTab, setActiveTab] = useState<"code" | "paper">("code");

  const handleScrollToDemo = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const elem = document.getElementById("demo");
    if (elem) {
      elem.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
      {/* Background Subtle Gradient & Grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-60 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#DA7756]/8 blur-[140px] pointer-events-none rounded-full" />
      
      <Container>
        {/* Eyebrow, Headline, Supporting Copy, Actions */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#222227] border border-white/10 mb-6">
            <span className="w-2 h-2 rounded-full bg-[#DA7756] animate-pulse" />
            <span className="text-[11px] md:text-xs font-mono uppercase tracking-widest text-[#9E9E99]">
              AUTONOMOUS MULTI-AGENT RESEARCH-TO-CODE COMPILER
            </span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-[#F4F3EE] font-heading leading-[1.08] mb-6">
            From research papers to{" "}
            <span className="text-[#DA7756] relative inline-block">
              executable systems
              <svg className="absolute -bottom-2 left-0 w-full h-2 text-[#DA7756]/40" viewBox="0 0 100 10" preserveAspectRatio="none">
                <path d="M0 5 Q 50 10 100 5" stroke="currentColor" strokeWidth="2" fill="none" />
              </svg>
            </span>
            .
          </h1>

          {/* Supporting Copy */}
          <p className="text-lg md:text-xl text-[#9E9E99] leading-relaxed max-w-2xl mx-auto mb-10 font-sans">
            {project.supportingCopy}
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="#demo"
              onClick={handleScrollToDemo}
              className="group inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#DA7756] text-[#F4F3EE] font-medium text-sm hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_25px_-4px_rgba(218,119,86,0.5)] hover:shadow-[0_0_30px_-2px_rgba(218,119,86,0.7)]"
            >
              <Play className="w-4 h-4 fill-current transition-transform duration-200 group-hover:scale-110" />
              <span>Watch the demo</span>
            </a>

            <a
              href="https://github.com/varunchandra10/Paper-2-Project"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#222227] hover:bg-[#292930] border border-white/10 hover:border-white/20 text-[#F4F3EE] font-medium text-sm transition-all duration-200"
            >
              <GithubIcon className="w-4 h-4 text-[#9E9E99]" />
              <span>Explore on GitHub</span>
              <ArrowRight className="w-4 h-4 text-[#71717A]" />
            </a>
          </div>
        </div>

        {/* Hero Visual: Side-by-Side Research-to-Code Transformation Window */}
        <div className="relative max-w-5xl mx-auto">
          {/* Subtle Outer Frame Glow */}
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-b from-[#DA7756]/20 to-transparent blur-xl -z-10" />

          <div className="rounded-2xl border border-white/10 bg-[#1C1C20] overflow-hidden shadow-2xl">
            {/* Window Chrome Header */}
            <div className="px-4 py-3 bg-[#131315] border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-white/10" />
                  <div className="w-3 h-3 rounded-full bg-white/10" />
                  <div className="w-3 h-3 rounded-full bg-white/10" />
                </div>
                <div className="h-4 w-px bg-white/10 mx-2" />
                <span className="text-xs font-mono text-[#9E9E99] flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-[#DA7756]" />
                  ruexis-compiler // attention_mechanism.pdf → pytorch_module.py
                </span>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#34D399]/10 border border-[#34D399]/25 text-[11px] font-mono text-[#34D399]">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>AST Syntax Valid</span>
                </span>
              </div>
            </div>

            {/* Split Content: Paper Input → Synthesized PyTorch */}
            <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-white/10 font-mono text-xs">
              {/* Left Column: Research Paper Methodology Contract (5 cols) */}
              <div className="lg:col-span-5 p-5 bg-[#18181B]/80 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
                    <span className="text-[11px] uppercase tracking-wider text-[#9E9E99] font-sans font-semibold flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-[#38BDF8]" />
                      Ingested Paper Spec
                    </span>
                    <span className="text-[10px] text-[#71717A]">arXiv:1706.03762</span>
                  </div>

                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-[#222227]/70 border border-white/5 font-sans">
                      <div className="text-[11px] text-[#71717A] mb-1 font-mono">Title</div>
                      <div className="text-xs font-medium text-[#F4F3EE]">Attention Is All You Need</div>
                      <div className="text-[11px] text-[#9E9E99] mt-1 line-clamp-2">
                        Scaled dot-product attention compute with multi-head projection layers.
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-[#222227]/70 border border-white/5">
                      <div className="text-[10px] text-[#71717A] uppercase tracking-wider mb-1.5">
                        Extracted Contract
                      </div>
                      <div className="space-y-1 text-[#9E9E99]">
                        <div className="flex justify-between">
                          <span className="text-[#DA7756]">d_model</span>
                          <span className="text-[#F4F3EE]">512</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#DA7756]">n_heads</span>
                          <span className="text-[#F4F3EE]">8 (d_k = 64)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#DA7756]">dropout</span>
                          <span className="text-[#F4F3EE]">0.1</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#DA7756]">scale_factor</span>
                          <span className="text-[#F4F3EE]">1 / sqrt(d_k)</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-[#222227]/70 border border-white/5">
                      <div className="text-[10px] text-[#71717A] uppercase tracking-wider mb-1">
                        Mathematical Definition
                      </div>
                      <div className="text-[#38BDF8] text-[11px]">
                        Attention(Q, K, V) = softmax(QKᵀ / √d_k) V
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] text-[#71717A] font-sans">
                  <span>Feasibility Check</span>
                  <span className="text-[#34D399] font-mono">Estimated VRAM: 1.4 GB</span>
                </div>
              </div>

              {/* Right Column: Synthesized PyTorch Implementation (7 cols) */}
              <div className="lg:col-span-7 bg-[#111113] p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
                    <span className="text-[11px] uppercase tracking-wider text-[#9E9E99] font-sans font-semibold flex items-center gap-2">
                      <Code2 className="w-3.5 h-3.5 text-[#DA7756]" />
                      Synthesized PyTorch Module
                    </span>
                    <span className="text-[10px] text-[#71717A]">models/multihead_attention.py</span>
                  </div>

                  <pre className="text-[11px] text-[#F4F3EE] leading-relaxed overflow-x-auto pb-2">
                    <code>
                      <span className="text-[#DA7756]">import</span> math{"\n"}
                      <span className="text-[#DA7756]">import</span> torch{"\n"}
                      <span className="text-[#DA7756]">import</span> torch.nn <span className="text-[#DA7756]">as</span> nn{"\n\n"}
                      <span className="text-[#DA7756]">class</span> <span className="text-[#38BDF8]">MultiHeadAttention</span>(nn.Module):{"\n"}
                      {"  "}<span className="text-[#71717A]">"""Synthesized directly from paper formal specifications."""</span>{"\n"}
                      {"  "}<span className="text-[#DA7756]">def</span> <span className="text-[#818CF8]">__init__</span>(self, d_model: int = <span className="text-[#FBBF24]">512</span>, n_heads: int = <span className="text-[#FBBF24]">8</span>, dropout: float = <span className="text-[#FBBF24]">0.1</span>):{"\n"}
                      {"    "}super().__init__(){"\n"}
                      {"    "}self.d_k = d_model // n_heads{"\n"}
                      {"    "}self.n_heads = n_heads{"\n"}
                      {"    "}self.q_proj = nn.Linear(d_model, d_model){"\n"}
                      {"    "}self.k_proj = nn.Linear(d_model, d_model){"\n"}
                      {"    "}self.v_proj = nn.Linear(d_model, d_model){"\n"}
                      {"    "}self.out_proj = nn.Linear(d_model, d_model){"\n"}
                      {"    "}self.dropout = nn.Dropout(dropout){"\n\n"}
                      {"  "}<span className="text-[#DA7756]">def</span> <span className="text-[#818CF8]">forward</span>(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor) -&gt; torch.Tensor:{"\n"}
                      {"    "}scores = torch.matmul(q, k.transpose(-<span className="text-[#FBBF24]">2</span>, -<span className="text-[#FBBF24]">1</span>)) / math.sqrt(self.d_k){"\n"}
                      {"    "}attn = torch.softmax(scores, dim=-<span className="text-[#FBBF24]">1</span>){"\n"}
                      {"    "}<span className="text-[#DA7756]">return</span> self.out_proj(torch.matmul(self.dropout(attn), v))
                    </code>
                  </pre>
                </div>

                <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[11px]">
                  <span className="text-[#9E9E99]">Python 3.11 AST Verifier</span>
                  <span className="text-[#34D399] font-mono">0 Syntax Errors // 100% Valid AST</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
