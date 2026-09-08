import React from 'react';

interface LoaderProps {
  message?: string;
  subtext?: string;
  className?: string;
}

export const Spinner: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => {
  return (
    <div className={`relative ${className} shrink-0 inline-flex items-center justify-center`}>
      <div className="absolute inset-0 rounded-full border-2 border-[var(--border-color)]" />
      <div className="absolute inset-0 rounded-full border-2 border-t-[var(--accent)] border-r-[var(--accent)]/40 animate-spin" />
    </div>
  );
};

export const SystemWideLoader: React.FC<LoaderProps> = ({ 
  message = 'Synthesizing Neural Workspace...', 
  subtext = 'Initializing local environment and model dependencies'
}) => {
  return (
    <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-[var(--bg-base)]/80 backdrop-blur-md animate-fade-in p-4 select-none">
      {/* Background Ambient Glow */}
      <div className="absolute w-72 h-72 bg-[var(--accent)]/10 rounded-full blur-3xl pointer-events-none animate-pulse-fast" />

      {/* Loader Modal Container */}
      <div className="relative flex flex-col items-center p-8 rounded-2xl border border-[var(--accent-border)] bg-[var(--bg-card)] text-[var(--text-main)] shadow-xl max-w-sm text-center">
        {/* HUD Corner Accents */}
        <div className="absolute top-2.5 left-2.5 w-2.5 h-2.5 border-t-2 border-l-2 border-[var(--accent)]" />
        <div className="absolute top-2.5 right-2.5 w-2.5 h-2.5 border-t-2 border-r-2 border-[var(--accent)]" />
        <div className="absolute bottom-2.5 left-2.5 w-2.5 h-2.5 border-b-2 border-l-2 border-[var(--accent)]" />
        <div className="absolute bottom-2.5 right-2.5 w-2.5 h-2.5 border-b-2 border-r-2 border-[var(--accent)]" />

        {/* Central Spinning Radar Ring */}
        <div className="relative w-16 h-16 mb-5 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-[var(--border-color)]" />
          <div className="absolute inset-0 rounded-full border-2 border-t-[var(--accent)] border-r-[var(--accent)]/80 animate-spin" />
          <div className="absolute inset-2 rounded-full border border-[var(--accent-border)] bg-[var(--accent-subtle)] animate-pulse" />
          <div className="w-2 h-2 rounded-full bg-[var(--accent)] shadow-[0_0_10px_var(--accent)]" />
        </div>

        {/* Status Messaging */}
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-[var(--text-main)] mb-1.5 flex items-center gap-2">
          {message}
        </h3>
        <p className="text-xs font-mono text-[var(--text-muted)] leading-relaxed">
          {subtext}
        </p>
      </div>
    </div>
  );
};