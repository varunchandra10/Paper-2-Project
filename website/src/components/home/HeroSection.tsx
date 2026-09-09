"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  ArrowRight, 
  Workflow, 
  Download,
  Terminal,
  Sparkles,
  ShieldCheck,
  Cpu,
  Monitor,
  CheckCircle2,
  ChevronRight,
  Layers
} from "lucide-react";

interface HeroSectionProps {
  onOpenDownload?: () => void;
}

export function HeroSection({ onOpenDownload }: HeroSectionProps) {
  const [selectedMascotId, setSelectedMascotId] = useState<string>("mr-nerdy");

  const mascots = [
    {
      id: "mr-nerdy",
      name: "Mr. Nerdy",
      role: "Lead Research Fellow",
      tag: "Companion 01",
      badge: "PyMuPDF + Docling",
      color: "#DA7756",
      image: "/mascots/mr_nerdy/mr_nerdy_standing.png",
      status: "Idle Standing",
    },
    {
      id: "ms-nerdy",
      name: "Ms. Nerdy",
      role: "Autonomous ML Scientist",
      tag: "Companion 02",
      badge: "8 LangGraph Agents",
      color: "#38BDF8",
      image: "/mascots/ms_nerdy/ms_nerdy_standing.png",
      status: "60 FPS FSM",
    },
    {
      id: "mr-nerd",
      name: "Mr. Nerd",
      role: "Win32 C-FFI Specialist",
      tag: "Companion 03",
      badge: "Taskbar Docked",
      color: "#A855F7",
      image: "/mascots/mr_nerd/mr_nerd_standing.png",
      status: "Shell32 Linked",
    },
    {
      id: "ms-nerd",
      name: "Ms. Nerd",
      role: "PyTorch Compiler Lead",
      tag: "Companion 04",
      badge: "100% AST Conformance",
      color: "#34D399",
      image: "/mascots/ms_nerd/ms_nerd_standing.png",
      status: "Zero Syntax Error",
    },
  ];

  const activeMascot = mascots.find((m) => m.id === selectedMascotId) || mascots[0];

  return (
    <section className="relative min-h-[85vh] flex items-center pt-28 pb-16 md:pt-36 md:pb-24 overflow-hidden bg-grid-pattern">
      
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/4 w-[600px] h-[350px] bg-[#DA7756]/10 rounded-full blur-[160px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[350px] bg-[#38BDF8]/8 rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          
          {/* ─────────────────────────────────────────────────────────────
              LEFT COLUMN: HERO CONTENT & CTAs (7 COLS)
          ───────────────────────────────────────────────────────────── */}
          <div className="lg:col-span-7 flex flex-col items-start text-left">
            
            {/* Top Pill Chip */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#222227]/90 border border-white/10 mb-6 backdrop-blur-md shadow-lg">
              <span className="w-2 h-2 rounded-full bg-[#DA7756] animate-pulse" />
              <span className="text-xs font-mono uppercase tracking-wider text-[#DA7756] font-bold">
                Autonomous Desktop Literature-to-PyTorch
              </span>
            </div>

            {/* Main Heading */}
            <h1 className="text-5xl sm:text-6xl md:text-7xl xl:text-8xl font-black tracking-tight font-heading text-[#F4F3EE] uppercase leading-none mb-3">
              RUEXIS <span className="text-[#DA7756] glow-accent">AI</span>
            </h1>

            {/* Acronym Subtitle */}
            <p className="text-xs sm:text-sm font-mono text-[#9E9E99] tracking-wider uppercase mb-5">
              <span className="text-[#DA7756] font-bold">R</span>esearch • <span className="text-[#DA7756] font-bold">U</span>nderstand • <span className="text-[#DA7756] font-bold">E</span>xtract • e<span className="text-[#DA7756] font-bold">X</span>amine • <span className="text-[#DA7756] font-bold">I</span>mplement • <span className="text-[#DA7756] font-bold">S</span>ynthesize
            </p>

            {/* Value Proposition Description */}
            <p className="max-w-2xl text-sm sm:text-base md:text-lg text-[#D4D4D8] leading-relaxed mb-8 font-sans">
              Autonomous local-first desktop platform converting complex scientific papers into verified, runnable PyTorch code with <span className="text-[#34D399] font-mono font-bold">100% AST syntax conformance</span> and native Win32 taskbar companion docking.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3.5 mb-10 w-full sm:w-auto">
              <button
                onClick={onOpenDownload}
                className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#DA7756] text-white font-semibold text-sm hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_30px_-5px_rgba(218,119,86,0.6)] hover:scale-[1.02] cursor-pointer w-full sm:w-auto"
              >
                <Download className="w-4 h-4" />
                <span>Download Windows Client</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <Link
                href="/#architecture"
                className="flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE] font-medium text-sm hover:bg-[#292930] hover:border-white/20 transition-all duration-200 w-full sm:w-auto"
              >
                <Workflow className="w-4 h-4 text-[#38BDF8]" />
                <span>Architecture Flowchart</span>
              </Link>

              <Link
                href="/#models-roadmap"
                className="flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl bg-[#1C1C20] border border-white/8 text-[#9E9E99] hover:text-[#F4F3EE] font-medium text-sm hover:border-white/15 transition-all w-full sm:w-auto"
              >
                <Cpu className="w-4 h-4 text-[#DA7756]" />
                <span>Models & Roadmap</span>
              </Link>
            </div>

            {/* Key Verified Metric Badges Row */}
            <div className="flex items-center gap-4 sm:gap-6 flex-wrap text-xs font-mono text-[#9E9E99] pt-5 border-t border-white/8 w-full">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#34D399]" />
                <span>48 / 48 Papers Synthesized</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#38BDF8]" />
                <span>0 AST Syntax Failures</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <Monitor className="w-3.5 h-3.5 text-[#DA7756]" />
                <span>Win32 C-FFI Taskbar Dock</span>
              </span>
            </div>

          </div>

          {/* ─────────────────────────────────────────────────────────────
              RIGHT COLUMN: 4 MASCOTS IN A BOXED NON-FLOATING SHOWCASE (5 COLS)
          ───────────────────────────────────────────────────────────── */}
          <div className="lg:col-span-5 w-full">
            <div className="rounded-3xl bg-[#1C1C20] border border-white/10 p-5 sm:p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden">
              
              {/* Box Top Header */}
              <div className="flex items-center justify-between pb-4 border-b border-white/8 mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                  </div>
                  <span className="text-xs font-mono font-bold text-[#F4F3EE] uppercase tracking-wider pl-2 border-l border-white/10">
                    Desktop Mascots
                  </span>
                </div>

                <span className="text-[10px] font-mono text-[#34D399] bg-[#34D399]/10 px-2.5 py-1 rounded-full border border-[#34D399]/20 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#34D399] animate-pulse" />
                  <span>Win32 Docked</span>
                </span>
              </div>

              {/* 2x2 Grid of the 4 Boxed Mascots */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {mascots.map((mascot) => {
                  const isSelected = selectedMascotId === mascot.id;

                  return (
                    <div
                      key={mascot.id}
                      onClick={() => setSelectedMascotId(mascot.id)}
                      className={`p-3 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col items-center justify-between relative group ${
                        isSelected
                          ? "bg-[#222227] border-[#DA7756] shadow-[0_0_20px_rgba(218,119,86,0.35)] ring-1.5 ring-[#DA7756]"
                          : "bg-[#18181B] border-white/8 hover:bg-[#222227]/90 hover:border-white/20"
                      }`}
                    >
                      {/* Top Tag & Status */}
                      <div className="w-full flex items-center justify-between text-[9px] font-mono mb-1">
                        <span 
                          className="font-bold px-1.5 py-0.5 rounded"
                          style={{ 
                            backgroundColor: `${mascot.color}15`, 
                            color: mascot.color 
                          }}
                        >
                          {mascot.tag}
                        </span>
                        <span className="text-[#71717A] truncate max-w-[80px]">
                          {mascot.badge.split(" ")[0]}
                        </span>
                      </div>

                      {/* Mascot Single Frame (Uncompressed, Natural Single Center Frame) */}
                      <div className="w-full h-32 sm:h-36 flex items-center justify-center my-1 relative">
                        <div
                          className="w-24 sm:w-28 h-full filter drop-shadow-[0_8px_16px_rgba(0,0,0,0.5)] transition-transform duration-200 group-hover:scale-105"
                          style={{
                            backgroundImage: `url(${mascot.image})`,
                            backgroundSize: "300% 100%",
                            backgroundPosition: "50% 50%",
                            backgroundRepeat: "no-repeat",
                          }}
                          title={mascot.name}
                        />
                      </div>

                      {/* Name & Role */}
                      <div className="w-full text-center pt-2 border-t border-white/5">
                        <div className="text-xs font-bold font-heading text-[#F4F3EE] group-hover:text-[#DA7756] transition-colors truncate">
                          {mascot.name}
                        </div>
                        <div className="text-[10px] font-mono text-[#9E9E99] truncate">
                          {mascot.role.split(" ")[0]} {mascot.role.split(" ")[1]}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bottom Card Footer with Mascot FSM Link */}
              <div className="p-3 rounded-xl bg-[#18181B] border border-white/5 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#DA7756]" />
                  <span className="text-[#D4D4D8] font-bold">{activeMascot.name} Active</span>
                </div>

                <Link
                  href="/#mascot"
                  className="text-[#DA7756] hover:underline flex items-center gap-1 font-semibold text-[11px]"
                >
                  <span>Test in FSM Workbench</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

            </div>
          </div>

        </div>
      </div>

    </section>
  );
}
