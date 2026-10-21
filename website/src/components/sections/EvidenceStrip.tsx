import React from "react";
import { Container } from "../layout/Container";
import { project } from "@/data/project";
import { Info } from "lucide-react";

export function EvidenceStrip() {
  return (
    <section className="py-12 border-y border-white/8 bg-[#131315]/80 relative z-10">
      <Container>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
          {project.evidence.map((item, idx) => (
            <div 
              key={idx} 
              className="p-5 rounded-xl bg-[#1C1C20]/50 border border-white/5 hover:border-white/10 transition-colors"
            >
              <div className="text-3xl md:text-4xl font-bold font-mono text-[#F4F3EE] mb-1.5 flex items-baseline gap-1">
                <span className="text-[#DA7756]">{item.metric}</span>
              </div>
              <div className="text-sm font-semibold text-[#F4F3EE] font-sans mb-1">
                {item.label}
              </div>
              <p className="text-xs text-[#9E9E99] leading-relaxed">
                {item.detail}
              </p>
            </div>
          ))}
        </div>

        {/* Honest Footnote / Clarification Note */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-[#71717A] text-center">
          <Info className="w-3.5 h-3.5 text-[#DA7756] shrink-0" />
          <span>
            Evaluation benchmark note: AST syntax validity verifies that synthesized files parse cleanly without syntax errors in Python 3.11. It does not guarantee mathematical reproduction or runtime convergence.
          </span>
        </div>
      </Container>
    </section>
  );
}
