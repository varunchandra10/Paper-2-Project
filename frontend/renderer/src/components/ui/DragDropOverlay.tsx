import React from 'react';
import { FiUploadCloud, FiFileText } from 'react-icons/fi';

interface DragDropOverlayProps {
  isDragging: boolean;
}

export const DragDropOverlay: React.FC<DragDropOverlayProps> = ({ isDragging }) => {
  if (!isDragging) return null;

  return (
    <div className="absolute inset-0 z-50 bg-background/85 backdrop-blur-md border-2 border-dashed border-brass/60 flex flex-col items-center justify-center gap-4 animate-fade-in pointer-events-none p-6">
      {/* HUD Accent Corner Brackets */}
      <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-brass/80" />
      <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-brass/80" />
      <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-brass/80" />
      <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-brass/80" />

      {/* Central Icon Container */}
      <div className="relative flex items-center justify-center">
        <div className="absolute -inset-2 rounded-2xl bg-brass/20 blur-xl animate-pulse-fast" />
        <div className="relative w-20 h-20 rounded-2xl bg-card border border-brass/40 flex items-center justify-center text-brass shadow-[0_0_25px_rgba(212,163,56,0.25)] transition-transform duration-300 scale-105">
          <FiUploadCloud className="text-4xl animate-bounce" />
        </div>
      </div>

      {/* Content Labels */}
      <div className="flex flex-col items-center gap-1.5 text-center">
        <span className="text-base font-bold font-mono text-foreground tracking-wider uppercase flex items-center gap-2">
          Drop Paper to Synthesize
        </span>
        <p className="text-xs font-mono text-muted-foreground max-w-xs">
          Release to extract research parameters, architecture build tree, and code requirements.
        </p>
      </div>

      {/* File Type Pill Indicators */}
      <div className="flex items-center gap-2 pt-1">
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-brass/10 border border-brass/30 text-brass">
          <FiFileText className="text-xs" /> .PDF
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-muted border border-border text-muted-foreground">
          <FiFileText className="text-xs" /> .DOCX
        </span>
      </div>
    </div>
  );
};