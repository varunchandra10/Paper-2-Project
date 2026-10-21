"use client";

import React from "react";
import { Container } from "../layout/Container";
import { Play, ArrowRight, ExternalLink } from "lucide-react";
import { GithubIcon } from "../ui/GithubIcon";
import { project } from "@/data/project";

export function FinalCTASection() {
  const handleScrollToDemo = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const elem = document.getElementById("demo");
    if (elem) {
      elem.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="py-24 md:py-36 relative overflow-hidden bg-gradient-to-b from-[#18181B] via-[#1C1C20] to-[#131315] border-t border-white/8">
      {/* Subtle Glow Backdrop */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#DA7756]/10 blur-[130px] pointer-events-none rounded-full" />

      <Container>
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#222227] border border-white/10 mb-6">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#DA7756]">
              OPEN RESEARCH PROJECT
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#F4F3EE] font-heading leading-tight mb-6">
            Explore the implementation.
          </h2>

          <p className="text-base md:text-lg text-[#9E9E99] leading-relaxed mb-10 max-w-xl mx-auto font-sans">
            Inspect the code, review the architecture, and see how the research-to-code compiler pipeline is assembled.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="https://github.com/varunchandra10/Paper-2-Project"
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#DA7756] text-[#F4F3EE] font-medium text-sm hover:bg-[#E48666] transition-all duration-200 shadow-[0_0_25px_-4px_rgba(218,119,86,0.5)] hover:shadow-[0_0_30px_-2px_rgba(218,119,86,0.7)]"
            >
              <GithubIcon className="w-4 h-4 text-white" />
              <span>View source on GitHub</span>
              <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </a>

            <a
              href="#demo"
              onClick={handleScrollToDemo}
              className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-[#222227] hover:bg-[#292930] border border-white/10 hover:border-white/20 text-[#F4F3EE] font-medium text-sm transition-all duration-200"
            >
              <Play className="w-4 h-4 fill-current text-[#9E9E99]" />
              <span>Watch the walkthrough</span>
            </a>
          </div>
        </div>
      </Container>
    </section>
  );
}
