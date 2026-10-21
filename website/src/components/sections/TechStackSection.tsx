import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";

export function TechStackSection() {
  return (
    <section className="py-20 md:py-28 bg-[#131315]/40 border-t border-white/8">
      <Container>
        <SectionHeading
          badge="Technology Stack"
          badgeVariant="neutral"
          title="Verified toolchain."
          highlightText="Zero superfluous bloat."
          description="Grouped by functional role across desktop client, orchestration runtime, vector index, and validation engines."
          align="center"
          className="mb-14"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {project.techStack.map((group) => (
            <div
              key={group.category}
              className="p-6 rounded-2xl bg-[#1C1C20] border border-white/8 flex flex-col justify-between"
            >
              <div>
                <h3 className="text-xs font-mono uppercase tracking-wider text-[#DA7756] mb-4 pb-2 border-b border-white/5">
                  {group.category}
                </h3>

                <div className="space-y-4">
                  {group.items.map((item) => (
                    <div key={item.name}>
                      <div className="flex items-baseline justify-between">
                        <span className="text-sm font-semibold text-[#F4F3EE] font-sans">
                          {item.name}
                        </span>
                        <span className="text-[11px] font-mono text-[#71717A]">
                          {item.role}
                        </span>
                      </div>
                      <p className="text-xs text-[#9E9E99] mt-0.5 font-sans leading-relaxed">
                        {item.note}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
