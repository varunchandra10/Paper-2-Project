import React from "react";
import Link from "next/link";
import Image from "next/image";
import { Terminal, Shield, Layers, FileCode, Workflow, HelpCircle, Cpu } from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";

export function Footer() {
  return (
    <footer className="bg-[#131315] border-t border-white/8 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/8">
          
          {/* Col 1: Brand & Synopsis */}
          <div className="md:col-span-1 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#222227] border border-white/10 p-1 flex items-center justify-center">
                <Image
                  src="/ruexis_logo.svg"
                  alt="RUEXIS AI Logo"
                  width={28}
                  height={28}
                  className="w-full h-full object-contain"
                />
              </div>
              <span className="font-heading font-bold text-lg text-[#F4F3EE]">
                RUEXIS <span className="text-[#DA7756]">AI</span>
              </span>
            </div>
            <p className="text-xs text-[#9E9E99] leading-relaxed max-w-sm mb-6 font-sans">
              <strong className="text-[#F4F3EE]">R</strong>esearch, <strong className="text-[#F4F3EE]">U</strong>nderstand, <strong className="text-[#F4F3EE]">E</strong>xtract, e<strong className="text-[#F4F3EE]">X</strong>amine, <strong className="text-[#F4F3EE]">I</strong>mplement, <strong className="text-[#F4F3EE]">S</strong>ynthesize. An autonomous agentic desktop platform converting scientific literature into verified PyTorch implementations.
            </p>
            <div className="flex items-center gap-2 text-[11px] font-mono text-[#71717A]">
              <span className="w-2 h-2 rounded-full bg-[#34D399] animate-pulse"></span>
              <span>Local-First Runtime Active</span>
            </div>
          </div>

          {/* Col 2: Navigation Links */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#F4F3EE] mb-4 font-semibold flex items-center gap-2">
              <Workflow className="w-3.5 h-3.5 text-[#DA7756]" />
              Navigation
            </h4>
            <ul className="space-y-2 text-xs text-[#9E9E99]">
              <li>
                <Link href="/#features" className="hover:text-[#DA7756] transition-colors">
                  System Features & Empirical Metrics
                </Link>
              </li>
              <li>
                <Link href="/#architecture" className="hover:text-[#DA7756] transition-colors">
                  Interactive Architecture Flowchart
                </Link>
              </li>
              <li>
                <Link href="/#mascot" className="hover:text-[#DA7756] transition-colors">
                  13-State Mascot FSM Engine
                </Link>
              </li>
              <li>
                <Link href="/#models-roadmap" className="hover:text-[#DA7756] transition-colors">
                  Models & Engineering Roadmap
                </Link>
              </li>
              <li>
                <Link href="/#faq" className="hover:text-[#DA7756] transition-colors">
                  Frequently Asked Questions
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Engine Specs */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#F4F3EE] mb-4 font-semibold flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[#38BDF8]" />
              Empirical Specs
            </h4>
            <ul className="space-y-2 text-xs text-[#9E9E99]">
              <li>48 / 48 Scientific Papers Ingested</li>
              <li>332 PyTorch Files Synthesized</li>
              <li>100% AST Syntax Conformance</li>
              <li>100% Local-First Offline Mode</li>
              <li>Win32 C-FFI Taskbar Docking</li>
              <li>Dual Code Engine (Gemini + Qwen)</li>
            </ul>
          </div>

          {/* Col 4: Platform Links */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#F4F3EE] mb-4 font-semibold flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-[#34D399]" />
              Open Source
            </h4>
            <div className="space-y-3 text-xs">
              <a
                href="https://github.com/varunchandra10/Paper-2-Project"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#222227] border border-white/10 text-[#F4F3EE] hover:border-white/20 transition-all w-full"
              >
                <GithubIcon className="w-3.5 h-3.5" />
                <span>GitHub Source Repository</span>
              </a>
              <Link
                href="/#models-roadmap"
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#222227] border border-white/10 text-[#F4F3EE] hover:border-[#DA7756]/50 hover:text-[#DA7756] transition-all w-full"
              >
                <Cpu className="w-3.5 h-3.5 text-[#DA7756]" />
                <span>Models & Roadmap</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom copyright */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#71717A] font-mono">
          <p>© 2026 RUEXIS AI Architecture. Engineered for Autonomous Academic Reasoning.</p>
          <div className="flex items-center gap-4">
            <span>Electron 34</span>
            <span>•</span>
            <span>React 19</span>
            <span>•</span>
            <span>FastAPI</span>
            <span>•</span>
            <span>LangGraph</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
