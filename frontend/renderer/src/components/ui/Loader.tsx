import React from 'react';

interface LoaderProps {
  message?: string;
  className?: string;
}

export const Spinner: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => {
  return (
    <div className={`relative ${className} shrink-0`}>
      <div className="absolute inset-0 rounded-full border-2 border-border" />
      <div className="absolute inset-0 rounded-full border-2 border-t-emerald-500 border-r-emerald-500/30 animate-spin" />
    </div>
  );
};

export const SystemWideLoader: React.FC<LoaderProps> = ({ message = 'Initializing local environment...' }) => {
  return (
    <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-foreground/10 backdrop-blur-md animate-fade-in">
      <div className="flex flex-col items-center p-8 rounded-2xl border border-border bg-card text-card-foreground shadow-2xl max-w-xs text-center">
        {/* Glowing Radar Ring */}
        <div className="relative w-14 h-14 mb-4 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-4 border-muted" />
          <div className="absolute inset-0 rounded-full border-4 border-t-emerald-500 border-r-emerald-500/20 animate-spin" />
          <div className="absolute inset-2.5 rounded-full bg-muted border border-border animate-pulse" />
        </div>
        <h3 className="text-sm font-sans font-semibold text-foreground tracking-wide mb-1">
          Please Wait
        </h3>
        <p className="text-xs font-sans text-muted-foreground leading-relaxed animate-pulse">
          {message}
        </p>
      </div>
    </div>
  );
};
