import React from 'react';
import { IconCpu, IconActivity } from '../../ui/Icons';

interface ServerMetricsBadgeProps {
  metrics: {
    cpu?: {
      processor?: string;
      cores?: number;
      usage_percent?: number;
      ram_total_gb?: number;
      ram_available_gb?: number;
    };
    gpu?: {
      name?: string;
      cuda_available?: boolean;
      vram_total_gb?: number;
      vram_free_gb?: number;
    };
    groq?: {
      status?: string;
      remaining_requests?: number;
    };
    openrouter?: {
      status?: string;
      remaining_credits?: number;
    };
  } | null;
}

export const ServerMetricsBadge: React.FC<ServerMetricsBadgeProps> = ({ metrics }) => {
  if (!metrics) return null;

  const gpuName = metrics.gpu?.name || 'Local Host Compute';
  const isCuda = metrics.gpu?.cuda_available ?? false;
  const cpuPercent = metrics.cpu?.usage_percent ?? 0;
  const ramTotal = metrics.cpu?.ram_total_gb ?? 16;
  const ramAvailable = metrics.cpu?.ram_available_gb ?? 8;

  return (
    <div className="bg-[var(--bg-card)] border app-border rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 font-mono text-[var(--accent)] font-semibold">
          <IconCpu className="text-sm" />
          <span>CPU: {cpuPercent}%</span>
          <span className="text-[var(--text-muted)]">({metrics.cpu?.cores || 8} cores)</span>
        </div>
        <div className="h-3 w-px bg-[var(--border-color)]" />
        <div className="flex items-center gap-1.5 font-mono text-[var(--text-main)]">
          <span>RAM:</span>
          <span className="text-emerald-400 font-bold">{ramAvailable} GB free</span>
          <span className="text-[var(--text-muted)]">/ {ramTotal} GB</span>
        </div>
      </div>

      <div className="flex items-center gap-2 font-mono">
        <IconActivity className="text-xs text-[var(--accent)]" />
        <span className="text-[var(--text-muted)]">GPU:</span>
        <span className={`font-semibold ${isCuda ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
          {gpuName} {isCuda ? '(CUDA Active)' : '(CPU Fallback)'}
        </span>
      </div>
    </div>
  );
};
