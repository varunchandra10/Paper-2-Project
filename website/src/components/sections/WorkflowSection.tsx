import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { ArrowRight, Check } from "lucide-react";

export function WorkflowSection() {
  return (
    <section id="workflow" className="py-20 md:py-32 bg-[#131315]/50 border-t border-white/8 scroll-mt-20">
      <Container>
        <SectionHeading
          badge="Research-to-Code Pipeline"
          badgeVariant="cyan"
          title="Eight deliberate stages."
          highlightText="From paper to verified code."
          description="RUEXIS AI replaces fragile end-to-end prompt engineering with an auditable, multi-phase compilation pipeline."
          align="center"
          className="mb-16"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
          {project.workflowStages.map((stage) => (
            <div
              key={stage.id}
              className="p-6 rounded-2xl bg-[#1C1C20] border border-white/8 hover:border-[#DA7756]/40 hover:bg-[#222227] transition-all duration-200 flex flex-col justify-between group"
            >
              <div>
                {/* Stage Header: Number & Tag */}
                <div className="flex items-center justify-between mb-4">
                  <span className="w-7 h-7 rounded-lg bg-[#222227] border border-white/10 group-hover:border-[#DA7756]/40 group-hover:text-[#DA7756] text-xs font-mono font-bold flex items-center justify-center text-[#9E9E99] transition-colors">
                    0{stage.id}
                  </span>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717A] group-hover:text-[#9E9E99] transition-colors">
                    Stage {stage.id}
                  </span>
                </div>

                {/* Stage Title */}
                <h3 className="text-lg font-bold text-[#F4F3EE] font-heading mb-1 group-hover:text-[#DA7756] transition-colors">
                  {stage.name}
                </h3>
                
                <div className="text-xs font-mono text-[#DA7756] mb-3">
                  {stage.tagline}
                </div>

                {/* Description */}
                <p className="text-xs md:text-sm text-[#9E9E99] leading-relaxed mb-6 font-sans">
                  {stage.description}
                </p>
              </div>

              {/* Stage Artifact Output */}
              <div className="pt-3 border-t border-white/5 flex items-center gap-2 text-[11px] font-mono text-[#71717A] group-hover:text-[#9E9E99]">
                <Check className="w-3.5 h-3.5 text-[#34D399] shrink-0" />
                <span className="truncate">{stage.output}</span>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
