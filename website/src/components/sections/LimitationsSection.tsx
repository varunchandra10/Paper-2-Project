import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { ShieldAlert } from "lucide-react";

export function LimitationsSection() {
  return (
    <section className="py-20 md:py-28 relative border-t border-white/8">
      <Container>
        <SectionHeading
          badge="Responsible AI & Scope"
          badgeVariant="amber"
          title="Limitations and operational boundaries."
          description="Honest engineering requires acknowledging assumptions, non-determinism, and safe execution practices."
          align="center"
          className="mb-14"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {project.limitations.map((item, idx) => (
            <div
              key={idx}
              className="p-6 md:p-8 rounded-2xl bg-[#1C1C20] border border-white/8 flex items-start gap-4"
            >
              <div className="w-9 h-9 rounded-xl bg-[#FBBF24]/10 border border-[#FBBF24]/20 flex items-center justify-center shrink-0 mt-0.5">
                <ShieldAlert className="w-4 h-4 text-[#FBBF24]" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#F4F3EE] font-heading mb-2">
                  {item.title}
                </h3>
                <p className="text-xs md:text-sm text-[#9E9E99] leading-relaxed font-sans">
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
