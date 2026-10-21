import React from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { 
  Monitor, 
  Workflow, 
  Bot, 
  Database, 
  ShieldCheck, 
  Network,
  Lock,
  Cloud
} from "lucide-react";

export function ArchitectureSection() {
  const { heading, subheading, layers } = project.architecture;

  const layerIcons = [
    <Monitor key="0" className="w-5 h-5 text-[#38BDF8]" />,
    <Workflow key="1" className="w-5 h-5 text-[#DA7756]" />,
    <Bot key="2" className="w-5 h-5 text-[#818CF8]" />,
    <Database key="3" className="w-5 h-5 text-[#34D399]" />,
    <ShieldCheck key="4" className="w-5 h-5 text-[#FBBF24]" />,
    <Network key="5" className="w-5 h-5 text-[#F4F3EE]" />,
  ];

  return (
    <section id="architecture" className="py-20 md:py-32 relative scroll-mt-20">
      <Container>
        <SectionHeading
          badge="System Architecture"
          badgeVariant="cyan"
          title={heading}
          description={subheading}
          align="center"
          className="mb-16"
        />

        <div className="max-w-4xl mx-auto space-y-4">
          {/* Top 5 Layers: Fully Local System */}
          <div className="p-4 rounded-xl bg-[#1C1C20]/40 border border-white/5 mb-6 flex items-center justify-between text-xs font-mono text-[#9E9E99]">
            <span className="flex items-center gap-2 text-[#34D399]">
              <Lock className="w-3.5 h-3.5" />
              <span>Local-First Execution Environment (On-Device)</span>
            </span>
            <span className="text-[#71717A]">Air-Gapped Core</span>
          </div>

          {layers.slice(0, 5).map((layer, idx) => (
            <div
              key={layer.name}
              className="p-6 rounded-2xl bg-[#1C1C20] border border-white/8 hover:border-white/15 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-[#222227] border border-white/10 flex items-center justify-center shrink-0">
                  {layerIcons[idx]}
                </div>
                <div>
                  <div className="text-base font-bold text-[#F4F3EE] font-heading">
                    {layer.name}
                  </div>
                  <div className="text-xs font-mono text-[#DA7756] mt-0.5">
                    {layer.tech}
                  </div>
                  <div className="text-xs text-[#9E9E99] mt-1.5 font-sans">
                    {layer.description}
                  </div>
                </div>
              </div>

              <div className="text-[11px] font-mono px-3 py-1 rounded-md bg-[#222227] border border-white/5 text-[#9E9E99] shrink-0">
                Layer 0{idx + 1}
              </div>
            </div>
          ))}

          {/* Privacy & Provider Boundary */}
          <div className="py-6 flex items-center gap-4">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />
            <div className="text-xs font-mono uppercase tracking-widest text-[#DA7756] px-4 py-1.5 rounded-full bg-[#DA7756]/10 border border-[#DA7756]/25 flex items-center gap-2">
              <Cloud className="w-3.5 h-3.5" />
              <span>Inference Gateway & Model Boundary</span>
            </div>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />
          </div>

          {/* Layer 6: Model Router */}
          <div className="p-6 rounded-2xl bg-[#222227] border border-[#DA7756]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-[#18181B] border border-white/10 flex items-center justify-center shrink-0">
                {layerIcons[5]}
              </div>
              <div>
                <div className="text-base font-bold text-[#F4F3EE] font-heading">
                  {layers[5].name}
                </div>
                <div className="text-xs font-mono text-[#DA7756] mt-0.5">
                  {layers[5].tech}
                </div>
                <div className="text-xs text-[#9E9E99] mt-1.5 font-sans">
                  {layers[5].description}
                </div>
              </div>
            </div>

            <div className="text-[11px] font-mono px-3 py-1 rounded-md bg-[#DA7756]/20 border border-[#DA7756]/30 text-[#DA7756] shrink-0 font-semibold">
              Flexible Routing
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
