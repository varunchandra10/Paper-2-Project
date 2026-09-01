import React from 'react';

interface LoaderProps {
  message?: string;
  subtext?: string;
  className?: string;
}

export const Spinner: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => {
  return (
    <div className={`relative ${className} shrink-0 inline-flex items-center justify-center`}>
      <div className="absolute inset-0 rounded-full border-2 border-border/40" />
      <div className="absolute inset-0 rounded-full border-2 border-t-brass border-r-brass/40 animate-spin" />
    </div>
  );
};

export const SystemWideLoader: React.FC<LoaderProps> = ({ 
  message = 'Synthesizing Neural Workspace...', 
  subtext = 'Initializing local environment and model dependencies'
}) => {
  return (
    <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-background/80 backdrop-blur-md animate-fade-in p-4 select-none">
      {/* Background Ambient Glow */}
      <div className="absolute w-72 h-72 bg-brass/10 rounded-full blur-3xl pointer-events-none animate-pulse-fast" />

      {/* Loader Modal Container */}
      <div className="relative flex flex-col items-center p-8 rounded-2xl border border-brass/30 bg-card text-card-foreground shadow-[0_0_50px_rgba(0,0,0,0.5)] max-w-sm text-center">
        {/* HUD Corner Accents */}
        <div className="absolute top-2.5 left-2.5 w-2.5 h-2.5 border-t-2 border-l-2 border-brass/70" />
        <div className="absolute top-2.5 right-2.5 w-2.5 h-2.5 border-t-2 border-r-2 border-brass/70" />
        <div className="absolute bottom-2.5 left-2.5 w-2.5 h-2.5 border-b-2 border-l-2 border-brass/70" />
        <div className="absolute bottom-2.5 right-2.5 w-2.5 h-2.5 border-b-2 border-r-2 border-brass/70" />

        {/* Central Spinning Radar Ring */}
        <div className="relative w-16 h-16 mb-5 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-border" />
          <div className="absolute inset-0 rounded-full border-2 border-t-brass border-r-synthesis/80 animate-spin" />
          <div className="absolute inset-2 rounded-full border border-brass/20 bg-brass/5 animate-pulse" />
          <div className="w-2 h-2 rounded-full bg-brass shadow-[0_0_10px_var(--brass)]" />
        </div>

        {/* Status Messaging */}
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-foreground mb-1.5 flex items-center gap-2">
          {message}
        </h3>
        <p className="text-xs font-mono text-muted-foreground leading-relaxed">
          {subtext}
        </p>
      </div>
    </div>
  );
};