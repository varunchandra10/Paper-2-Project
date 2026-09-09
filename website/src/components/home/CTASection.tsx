"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Copy, Check, Download, Layers, ShieldCheck } from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";

interface CTASectionProps {
  onOpenDownload?: () => void;
}

export function CTASection({ onOpenDownload }: CTASectionProps) {
  const [copied, setCopied] = useState(false);
  const command = "git clone https://github.com/varunchandra10/Paper-2-Project.git";

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-24 bg-[#18181B] border-t border-white/8 relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none -z-10">
        <div className="w-[500px] h-[300px] bg-[#DA7756]/10 rounded-full blur-[140px]" />
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#222227] border border-white/10 text-xs font-mono text-[#DA7756] mb-6 font-semibold">
          <span className="w-2 h-2 rounded-full bg-[#DA7756] animate-pulse" />
          AUTONOMOUS RESEARCH WORKBENCH
        </div>

        <h2 className="text-3xl sm:text-5xl font-bold text-[#F4F3EE] font-heading tracking-tight mb-6">
          Ready to Turn Research Papers <br className="hidden sm:inline" />
          Into <span className="text-[#DA7756] glow-accent">Verified PyTorch Code?</span>
        </h2>

        <p className="text-base sm:text-lg text-[#9E9E99] max-w-2xl mx-auto mb-10 leading-relaxed font-sans">
          Deploy the local-first runtime on your machine, test the 13-state animated mascot overlay, or download the pre-compiled native desktop client.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
          {/* Download App Button */}
          <button
            onClick={onOpenDownload}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#DA7756] text-white font-semibold text-sm hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_25px_rgba(218,119,86,0.5)] cursor-pointer hover:scale-[1.02]"
          >
            <Download className="w-4 h-4" />
            <span>Download Desktop Client (Win32 x64)</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <Link
            href="/#mascot"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-[#222227] border border-white/10 text-[#F4F3EE] font-semibold text-sm hover:bg-[#292930] hover:border-white/20 transition-all"
          >
            <Layers className="w-4 h-4 text-[#DA7756]" />
            <span>Test Mascot Workbench</span>
          </Link>

          <a
            href="https://github.com/varunchandra10/Paper-2-Project"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-[#1C1C20] border border-white/8 text-[#9E9E99] hover:text-[#F4F3EE] font-semibold text-sm hover:border-white/20 transition-all"
          >
            <GithubIcon className="w-4 h-4" />
            <span>GitHub Repository</span>
          </a>
        </div>

        {/* Git Clone Box */}
        <div className="max-w-md mx-auto p-3 rounded-xl bg-[#131315] border border-white/10 flex items-center justify-between gap-3 text-xs font-mono shadow-inner">
          <span className="text-[#9E9E99] truncate text-left pl-2">
            $ {command}
          </span>
          <button
            onClick={handleCopy}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-[#F4F3EE] transition-colors shrink-0 cursor-pointer"
            title="Copy command"
          >
            {copied ? <Check className="w-4 h-4 text-[#34D399]" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </section>
  );
}
