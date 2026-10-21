import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { 
  Bot, 
  Cpu, 
  Code2, 
  CheckCircle2, 
  Database, 
  Network 
} from "lucide-react";

export function FeaturesSection() {
  const iconMap: Record<string, React.ReactNode> = {
    "agentic-orchestration": <Bot className="w-5 h-5 text-[#DA7756]" />,
    "feasibility-profiling": <Cpu className="w-5 h-5 text-[#38BDF8]" />,
    "pytorch-synthesis": <Code2 className="w-5 h-5 text-[#DA7756]" />,
    "ast-validation": <CheckCircle2 className="w-5 h-5 text-[#34D399]" />,
    "local-retrieval": <Database className="w-5 h-5 text-[#818CF8]" />,
    "multi-model-router": <Network className="w-5 h-5 text-[#FBBF24]" />,
  };

  return (
    <section id="features" className="py-20 md:py-32 relative scroll-mt-20">
      <Container>
        <SectionHeading
          badge="Core Capabilities"
          badgeVariant="purple"
          title="Engineered for reproducibility."
          highlightText="Grounding over guesswork."
          description="Six key capabilities that allow RUEXIS AI to translate mathematical notation into structured PyTorch code without hallucinations."
          align="center"
          className="mb-16"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {project.features.map((feature) => (
            <div
              key={feature.id}
              className="p-8 rounded-2xl bg-[#1C1C20] border border-white/8 hover:border-[#DA7756]/40 hover:bg-[#222227] transition-all duration-200 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="w-10 h-10 rounded-xl bg-[#222227] border border-white/10 flex items-center justify-center group-hover:scale-105 transition-transform">
                    {iconMap[feature.id]}
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded-md bg-white/5 text-[#9E9E99] border border-white/5">
                    {feature.highlight}
                  </span>
                </div>

                <div className="text-[11px] font-mono uppercase tracking-wider text-[#71717A] mb-1">
                  {feature.category}
                </div>

                <h3 className="text-xl font-bold text-[#F4F3EE] font-heading mb-3 group-hover:text-[#DA7756] transition-colors">
                  {feature.title}
                </h3>

                <p className="text-sm text-[#9E9E99] leading-relaxed font-sans">
                  {feature.description}
                </p>
              </div>

              <div className="mt-8 pt-4 border-t border-white/5 flex items-center justify-between text-xs text-[#71717A]">
                <span>Status</span>
                <span className="text-[#34D399] font-mono">Implemented & Validated</span>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
