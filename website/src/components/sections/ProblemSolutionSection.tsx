import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";

export function ProblemSolutionSection() {
  const { heading, problem, solution } = project.problemSolution;

  return (
    <section className="py-20 md:py-32 relative">
      <Container>
        <SectionHeading
          badge="Problem & Approach"
          badgeVariant="accent"
          title={heading}
          align="center"
          className="mb-16"
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          {/* Left Column: The Problem */}
          <div className="p-8 md:p-10 rounded-2xl bg-[#1C1C20] border border-white/8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 text-xs font-mono uppercase tracking-wider text-[#F87171] mb-4">
                <AlertCircle className="w-4 h-4" />
                <span>The Reproduction Bottleneck</span>
              </div>

              <h3 className="text-xl md:text-2xl font-bold text-[#F4F3EE] font-heading mb-4 leading-snug">
                {problem.title}
              </h3>

              <p className="text-sm md:text-base text-[#9E9E99] leading-relaxed mb-8">
                {problem.description}
              </p>

              <div className="space-y-3.5">
                {problem.points.map((point, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#F87171] mt-2 shrink-0" />
                    <span className="text-sm text-[#9E9E99] leading-relaxed">
                      {point}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/5 text-xs text-[#71717A] italic">
              Manual re-implementation often results in subtle tensor shape bugs and silent divergence.
            </div>
          </div>

          {/* Right Column: The RUEXIS Solution */}
          <div className="p-8 md:p-10 rounded-2xl bg-[#222227] border border-[#DA7756]/30 shadow-xl flex flex-col justify-between relative overflow-hidden">
            {/* Subtle Accent Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#DA7756]/10 blur-3xl pointer-events-none rounded-full" />

            <div>
              <div className="flex items-center gap-2.5 text-xs font-mono uppercase tracking-wider text-[#DA7756] mb-4">
                <CheckCircle2 className="w-4 h-4" />
                <span>The Staged Architecture</span>
              </div>

              <h3 className="text-xl md:text-2xl font-bold text-[#F4F3EE] font-heading mb-4 leading-snug">
                {solution.title}
              </h3>

              <p className="text-sm md:text-base text-[#9E9E99] leading-relaxed mb-8">
                {solution.description}
              </p>

              <div className="space-y-3.5">
                {solution.points.map((point, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#DA7756] mt-2 shrink-0" />
                    <span className="text-sm text-[#F4F3EE] leading-relaxed">
                      {point}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/10 text-xs text-[#9E9E99] flex items-center gap-2">
              <span className="text-[#DA7756] font-mono">Explicit contracts</span>
              <span>enable auditability and modular code verification.</span>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
