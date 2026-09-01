import React from 'react';

interface SkinLoaderProps {
  type?: 'hardware' | 'chat' | 'document' | 'model' | 'list';
}

// Shared skeleton bar class — theme-aware, visible in both Light & Dark
const S = 'bg-[var(--text-muted)]/20 rounded';

export const SkinLoader: React.FC<SkinLoaderProps> = ({ type = 'hardware' }) => {
  if (type === 'hardware') {
    return (
      <div className="space-y-2 animate-pulse font-mono select-none">
        {/* CPU Skeleton Card */}
        <div className="p-2 rounded-lg bg-[var(--bg-base)] border app-border space-y-2">
          <div className={`h-2 w-24 ${S}`} />
          <div className={`h-2.5 w-36 ${S}`} />
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <div className={`h-2 w-12 ${S}`} />
              <div className={`h-2 w-16 ${S}`} />
            </div>
            <div className="flex justify-between">
              <div className={`h-2 w-14 ${S}`} />
              <div className={`h-2 w-10 ${S}`} />
            </div>
            <div className="flex justify-between">
              <div className={`h-2 w-14 ${S}`} />
              <div className={`h-2 w-8 ${S}`} />
            </div>
            <div className="flex justify-between">
              <div className={`h-2 w-16 ${S}`} />
              <div className={`h-2 w-12 ${S}`} />
            </div>
          </div>
        </div>

        {/* GPU Skeleton Card */}
        <div className="p-2 rounded-lg bg-[var(--bg-base)] border app-border space-y-2">
          <div className={`h-2 w-28 ${S}`} />
          <div className={`h-2.5 w-40 ${S}`} />
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <div className={`h-2 w-20 ${S}`} />
              <div className={`h-2 w-14 ${S}`} />
            </div>
            <div className="flex justify-between">
              <div className={`h-2 w-14 ${S}`} />
              <div className={`h-2 w-10 ${S}`} />
            </div>
            <div className="flex justify-between">
              <div className={`h-2 w-14 ${S}`} />
              <div className={`h-2 w-10 ${S}`} />
            </div>
          </div>
        </div>

        <div className={`h-6 w-full ${S} rounded-md`} />
      </div>
    );
  }

  if (type === 'chat') {
    return (
      <div className="space-y-1.5 animate-pulse p-2 select-none">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-2.5 rounded-xl border app-border bg-[var(--bg-card)] space-y-1.5">
            <div className="flex items-center justify-between">
              <div className={`h-2.5 ${S} w-3/4`} />
              <div className={`h-2 ${S} w-8`} />
            </div>
            <div className={`h-2 ${S} w-1/2`} />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'document') {
    return (
      <div className="space-y-1.5 animate-pulse p-2 select-none">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-2.5 p-2 rounded-xl border app-border bg-[var(--bg-card)]">
            <div className={`w-8 h-8 rounded-lg ${S} shrink-0`} />
            <div className="flex flex-col flex-1 gap-1.5">
              <div className={`h-2.5 ${S} w-4/5`} />
              <div className={`h-2 ${S} w-1/2`} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'model') {
    return (
      <div className="space-y-1.5 animate-pulse p-1 select-none">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-start gap-2.5 p-2 rounded-xl border app-border bg-[var(--bg-card)]">
            <div className={`w-6 h-6 rounded-lg ${S} shrink-0`} />
            <div className="flex flex-col flex-1 gap-1.5">
              <div className="flex justify-between items-center">
                <div className={`h-2.5 ${S} w-1/2`} />
                <div className={`h-2 ${S} w-8`} />
              </div>
              <div className={`h-2 ${S} w-4/5`} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Generic List Shimmer Loader
  return (
    <div className="space-y-2 animate-pulse p-2">
      <div className={`h-10 ${S} rounded-lg w-full`} />
      <div className={`h-10 ${S} rounded-lg w-full`} />
      <div className={`h-10 ${S} rounded-lg w-full`} />
    </div>
  );
};
