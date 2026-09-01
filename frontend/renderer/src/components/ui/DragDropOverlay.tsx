import React from 'react';
import { IconUploadCloud, IconFileText } from './Icons';

interface DragDropOverlayProps {
  isDragging: boolean;
}

export const DragDropOverlay: React.FC<DragDropOverlayProps> = ({ isDragging }) => {
  if (!isDragging) return null;

  return (
    <div className="absolute inset-0 z-50 bg-[var(--bg-base)]/85 backdrop-blur-md border-2 border-dashed border-[var(--accent)] flex flex-col items-center justify-center gap-4 animate-fade-in pointer-events-none p-6 select-none">
      {/* HUD Accent Corner Brackets */}
      <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-[var(--accent)]" />
      <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-[var(--accent)]" />
      <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-[var(--accent)]" />
      <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-[var(--accent)]" />

      {/* Central Icon Container */}
      <div className="relative flex items-center justify-center">
        <div className="absolute -inset-2 rounded-2xl bg-[var(--accent-subtle)] blur-xl animate-pulse" />
        <div className="relative w-20 h-20 rounded-2xl bg-[var(--bg-card)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] shadow-lg transition-transform duration-300 scale-105">
          <IconUploadCloud className="text-4xl animate-bounce" />
        </div>
      </div>

      {/* Content Labels */}
      <div className="flex flex-col items-center gap-1.5 text-center">
        <span className="text-base font-bold font-mono text-[var(--text-main)] tracking-wider uppercase flex items-center gap-2">
          Drop Paper to Synthesize
        </span>
        <p className="text-xs font-mono text-[var(--text-muted)] max-w-xs">
          Release to extract research parameters, architecture build tree, and code requirements.
        </p>
      </div>

      {/* File Type Pill Indicators */}
      <div className="flex items-center gap-2 pt-1">
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)]">
          <IconFileText className="text-xs" /> .PDF
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)]">
          <IconFileText className="text-xs" /> .DOCX
        </span>
      </div>
    </div>
  );
};