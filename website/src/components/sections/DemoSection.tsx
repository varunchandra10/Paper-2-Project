"use client";

import React, { useRef, useState } from "react";
import { Container } from "../layout/Container";
import { SectionHeading } from "../ui/SectionHeading";
import { project } from "@/data/project";
import { Play, Pause, RotateCcw, Volume2, VolumeX, Maximize2, Clock } from "lucide-react";

export function DemoSection() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const jumpToChapter = (seconds: number, index: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = seconds;
    videoRef.current.play().catch(() => {});
    setIsPlaying(true);
    setActiveChapter(index);
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const current = videoRef.current.currentTime;
    const idx = project.demoChapters.findIndex((c, i) => {
      const nextTime = project.demoChapters[i + 1]?.seconds || 9999;
      return current >= c.seconds && current < nextTime;
    });
    if (idx !== -1 && idx !== activeChapter) {
      setActiveChapter(idx);
    }
  };

  const currentChapter = project.demoChapters[activeChapter] || project.demoChapters[0];

  return (
    <section id="demo" className="py-20 md:py-32 bg-[#131315]/60 border-t border-white/8 scroll-mt-20">
      <Container>
        <SectionHeading
          badge="Product Walkthrough"
          badgeVariant="accent"
          title="See the research-to-code workflow in action."
          description="A complete 2-minute walkthrough showing paper ingestion, methodology extraction, PyTorch synthesis, and AST verification."
          align="center"
          className="mb-14"
        />

        <div className="max-w-5xl mx-auto">
          {/* Main Video Frame */}
          <div className="rounded-2xl border border-white/10 bg-[#1C1C20] overflow-hidden shadow-2xl relative group">
            <video
              ref={videoRef}
              poster="/videos/ruexis-demo-poster.webp"
              preload="metadata"
              className="w-full aspect-video object-cover bg-[#111113]"
              controls
              playsInline
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onTimeUpdate={handleTimeUpdate}
            >
              <source src="/videos/ruexis-demo.mp4" type="video/mp4" />
              Your browser does not support HTML5 video.
            </video>

            {/* Custom Play Overlay Button (Visible when paused) */}
            {!isPlaying && (
              <button
                onClick={togglePlay}
                aria-label="Play demo video"
                className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] transition-all hover:bg-black/20 group cursor-pointer"
              >
                <div className="w-20 h-20 rounded-full bg-[#DA7756] text-white flex items-center justify-center shadow-2xl transform transition-transform group-hover:scale-110">
                  <Play className="w-9 h-9 fill-current ml-1" />
                </div>
              </button>
            )}
          </div>

          {/* Interactive Chapter Markers */}
          <div className="mt-8">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-mono uppercase tracking-wider text-[#9E9E99] flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-[#DA7756]" />
                <span>Walkthrough Chapters</span>
              </div>
              {currentChapter && (
                <div className="text-xs text-[#DA7756] font-mono">
                  Current: {currentChapter.title} ({currentChapter.time})
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {project.demoChapters.map((chapter, idx) => {
                const isActive = activeChapter === idx;
                return (
                  <button
                    key={chapter.seconds}
                    onClick={() => jumpToChapter(chapter.seconds, idx)}
                    className={`p-3 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                      isActive
                        ? "bg-[#DA7756]/15 border-[#DA7756] text-[#F4F3EE] shadow-sm ring-1 ring-[#DA7756]/40"
                        : "bg-[#1C1C20] border-white/8 hover:border-white/15 text-[#9E9E99] hover:text-[#F4F3EE]"
                    }`}
                  >
                    <div className="text-[11px] font-mono text-[#DA7756] font-semibold mb-1">
                      {chapter.time}
                    </div>
                    <div className="text-xs font-medium truncate font-sans text-[#F4F3EE]">
                      {chapter.title}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Active Chapter Description Card */}
            {currentChapter && (
              <div className="mt-3 p-3.5 rounded-xl bg-[#1C1C20]/60 border border-white/6 text-xs text-[#9E9E99] flex items-center gap-2">
                <span className="font-mono text-[#DA7756] shrink-0 font-semibold">{currentChapter.time}</span>
                <span>—</span>
                <span className="text-[#F4F3EE]">{currentChapter.description}</span>
              </div>
            )}
          </div>
        </div>
      </Container>
    </section>
  );
}
