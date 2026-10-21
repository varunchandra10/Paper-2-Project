import React from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroSection } from "@/components/sections/HeroSection";
import { EvidenceStrip } from "@/components/sections/EvidenceStrip";
import { ProblemSolutionSection } from "@/components/sections/ProblemSolutionSection";
import { WorkflowSection } from "@/components/sections/WorkflowSection";
import { FeaturesSection } from "@/components/sections/FeaturesSection";
import { DemoSection } from "@/components/sections/DemoSection";
import { ArchitectureSection } from "@/components/sections/ArchitectureSection";
import { TechStackSection } from "@/components/sections/TechStackSection";
import { LimitationsSection } from "@/components/sections/LimitationsSection";
import { FinalCTASection } from "@/components/sections/FinalCTASection";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-[#18181B] text-[#F4F3EE] selection:bg-[#DA7756]/30 selection:text-[#F4F3EE]">
      <Navbar />

      <main className="flex-1">
        <HeroSection />
        <EvidenceStrip />
        <ProblemSolutionSection />
        <WorkflowSection />
        <FeaturesSection />
        <DemoSection />
        <ArchitectureSection />
        <TechStackSection />
        <LimitationsSection />
        <FinalCTASection />
      </main>

      <Footer />
    </div>
  );
}
