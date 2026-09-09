"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroSection } from "@/components/home/HeroSection";
import { FeaturesSection } from "@/components/home/FeaturesSection";
import { ArchitectureSection } from "@/components/home/ArchitectureSection";
import { MascotFSMSection } from "@/components/home/MascotFSMSection";
import { ModelsAndRoadmapSection } from "@/components/home/ModelsAndRoadmapSection";
import { FAQSection } from "@/components/home/FAQSection";
import { CTASection } from "@/components/home/CTASection";
import { DownloadModal } from "@/components/ui/DownloadModal";

export default function Home() {
  const [isDownloadOpen, setIsDownloadOpen] = useState(false);

  return (
    <div className="flex flex-col min-h-screen bg-[#18181B] text-[#F4F3EE]">
      <Navbar onOpenDownload={() => setIsDownloadOpen(true)} />
      
      <main className="flex-1">
        <HeroSection onOpenDownload={() => setIsDownloadOpen(true)} />
        <FeaturesSection />
        <ArchitectureSection />
        <MascotFSMSection />
        <ModelsAndRoadmapSection />
        <FAQSection />
        <CTASection onOpenDownload={() => setIsDownloadOpen(true)} />
      </main>

      <Footer />

      {/* 1-Week Countdown Release Modal */}
      <DownloadModal
        isOpen={isDownloadOpen}
        onClose={() => setIsDownloadOpen(false)}
      />
    </div>
  );
}
