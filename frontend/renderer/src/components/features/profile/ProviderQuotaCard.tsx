import React from 'react';
import { IconInfo } from '../../ui/Icons';

export interface QuotaMetric {
  label: string;
  refreshMessage?: string;
  remainingPct?: number | null;
  valueDisplay?: string;
}

interface ProviderQuotaCardProps {
  title: string;
  tooltip: string;
  primaryMetric: QuotaMetric;
  secondaryMetric?: QuotaMetric;
  consoleBadge?: {
    text: string;
    subtext: string;
  };
}

export const renderCircularProgress = (pct: number) => {
  const clamped = Math.max(0, Math.min(100, pct));
  const radius = 10;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clamped / 100) * circumference;

  let strokeColor = 'var(--accent)';
  if (clamped <= 15) {
    strokeColor = '#ef4444'; // Red-500
  } else if (clamped <= 50) {
    strokeColor = '#f59e0b'; // Amber-500
  }

  return (
    <div className="relative w-6 h-6 flex items-center justify-center shrink-0">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 24 24">
        <circle
          cx="12"
          cy="12"
          r={radius}
          stroke="var(--border-color)"
          strokeWidth="2.5"
          fill="transparent"
        />
        <circle
          cx="12"
          cy="12"
          r={radius}
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-500"
        />
      </svg>
    </div>
  );
};

export const ProviderQuotaCard: React.FC<ProviderQuotaCardProps> = ({
  title,
  tooltip,
  primaryMetric,
  secondaryMetric,
  consoleBadge,
}) => {
  const renderMetricValue = (metric: QuotaMetric) => {
    if (metric.remainingPct !== undefined && metric.remainingPct !== null) {
      return (
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[12px] font-semibold font-mono text-[var(--text-main)]">
            {metric.remainingPct}%
          </span>
          {renderCircularProgress(metric.remainingPct)}
        </div>
      );
    }
    if (metric.valueDisplay) {
      return (
        <div className="flex items-center shrink-0">
          <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] truncate max-w-[90px]">
            {metric.valueDisplay}
          </span>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-1.5 text-[12px] font-semibold text-[var(--text-main)] font-sans">
        <span>{title}</span>
        <span
          className="text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors cursor-help inline-flex items-center"
          data-tooltip={tooltip}
          data-tooltip-pos="bottom-right"
        >
          <IconInfo className="text-xs" />
        </span>
      </div>

      <div className="bg-[var(--bg-base)] border app-border rounded-xl p-3.5 flex flex-col justify-between flex-1 gap-3">
        {/* Primary Metric Row */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-col min-w-0">
            <span className="text-[11.5px] font-semibold text-[var(--text-main)]">
              {primaryMetric.label}
            </span>
            <span className="text-[10.5px] text-[var(--text-muted)] mt-0.5 leading-snug line-clamp-2">
              {primaryMetric.refreshMessage || 'Limit fully available.'}
            </span>
          </div>
          {renderMetricValue(primaryMetric)}
        </div>

        {/* Secondary Metric Row */}
        {secondaryMetric && (
          <div className="flex items-center justify-between gap-3 pt-2.5 border-t app-border">
            <div className="flex flex-col min-w-0">
              <span className="text-[11.5px] font-semibold text-[var(--text-main)]">
                {secondaryMetric.label}
              </span>
              <span className="text-[10.5px] text-[var(--text-muted)] mt-0.5 leading-snug line-clamp-2">
                {secondaryMetric.refreshMessage || 'Limit fully available.'}
              </span>
            </div>
            {renderMetricValue(secondaryMetric)}
          </div>
        )}

        {/* Console Telemetry Row */}
        {consoleBadge && (
          <div className="pt-2 border-t app-border flex items-center justify-between text-[10px] font-mono text-[var(--accent)] bg-[var(--accent-subtle)] px-2.5 py-1.5 rounded-lg border border-[var(--accent-border)]">
            <span className="truncate">{consoleBadge.text}</span>
            <span className="opacity-70 shrink-0 ml-1">{consoleBadge.subtext}</span>
          </div>
        )}
      </div>
    </div>
  );
};
