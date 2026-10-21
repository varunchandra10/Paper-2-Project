import React, { useState } from 'react';
import { IconInfo2, IconClose } from '../../ui/Icons';

export interface ExtractedParamMeta {
  value: string | number | boolean;
  status: 'EXPLICIT' | 'INFERRED' | 'DERIVED' | 'ASSUMED' | 'DEFAULT' | 'UNKNOWN' | string;
  confidence?: number;
  evidence_quote?: string | null;
  source_section?: string | null;
  grounding?: string | null;
  evidence_strength?: string;
}

interface ParameterConfigFormProps {
  customParams: Record<string, string>;
  extractedParams?: Record<string, ExtractedParamMeta> | null;
  onChange: (params: Record<string, string>) => void;
  onConfirm: () => void;
  confirmLabel?: string;
  compactMode?: boolean;
  activeFilter?: 'ALL' | 'EXPLICIT' | 'INFERRED' | 'DEFAULT' | null;
}

export const ParameterConfigForm: React.FC<ParameterConfigFormProps> = ({
  customParams,
  extractedParams,
  onChange,
  onConfirm,
  confirmLabel = 'Confirm & Run Feasibility Check',
  compactMode = false,
  activeFilter = 'ALL',
}) => {
  const [activeTooltipParam, setActiveTooltipParam] = useState<string | null>(null);

  const getResolvedStatus = (status?: string): 'EXPLICIT' | 'INFERRED' | 'DEFAULT' => {
    if (!status) return 'DEFAULT';
    const upper = status.toUpperCase();
    if (upper === 'EXPLICIT') return 'EXPLICIT';
    if (upper === 'INFERRED' || upper === 'DERIVED') return 'INFERRED';
    return 'DEFAULT';
  };

  const getStatusBadgeStyles = (status?: string) => {
    const resolved = getResolvedStatus(status);
    switch (resolved) {
      case 'EXPLICIT':
        return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 font-bold';
      case 'INFERRED':
        return 'border-amber-500/40 bg-amber-500/10 text-amber-400 font-bold';
      case 'DEFAULT':
      default:
        return 'border-dashed border-rose-500/40 bg-rose-500/10 text-rose-400 font-bold';
    }
  };

  const getCardBorderStyles = (status?: string) => {
    const resolved = getResolvedStatus(status);
    switch (resolved) {
      case 'EXPLICIT':
        return 'border-emerald-500/40 bg-emerald-500/[0.03] hover:border-emerald-500/70 focus-within:border-emerald-400';
      case 'INFERRED':
        return 'border-amber-500/40 bg-amber-500/[0.03] hover:border-amber-500/70 focus-within:border-amber-400';
      case 'DEFAULT':
      default:
        return 'border-dashed border-rose-500/40 bg-rose-500/[0.03] hover:border-rose-500/70 focus-within:border-rose-400';
    }
  };

  const handleFieldChange = (key: string, value: string) => {
    onChange({
      ...customParams,
      [key]: value,
    });
  };

  if (compactMode) {
    const compactKeys = ['learning_rate', 'batch_size', 'optimizer', 'loss'];
    return (
      <div className="w-full max-w-xs flex flex-col gap-2 bg-[var(--bg-base)]/80 p-3 rounded-lg border app-border text-left">
        <span className="text-[9px] font-mono font-bold text-[var(--accent)] uppercase">
          Hyperparameter Review (Human-in-Loop)
        </span>
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          {compactKeys.map((key) => {
            const item = extractedParams?.[key];
            const resolved = getResolvedStatus(item?.status);
            return (
              <div key={key} className="flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <label className="text-[8px] font-mono text-[var(--text-muted)] capitalize">
                    {key.replace('_', ' ')}
                  </label>
                  <span
                    className={`text-[7px] font-mono px-1 py-0.2 rounded border ${getStatusBadgeStyles(
                      item?.status
                    )}`}
                  >
                    {resolved}
                  </span>
                </div>
                <input
                  type="text"
                  value={customParams[key] || ''}
                  onChange={(e) => handleFieldChange(key, e.target.value)}
                  className={`bg-[var(--bg-card)] border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none ${getCardBorderStyles(
                    item?.status
                  )}`}
                />
              </div>
            );
          })}
        </div>
        <button
          type="button"
          onClick={onConfirm}
          className="mt-2 text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
        >
          {confirmLabel}
        </button>
      </div>
    );
  }

  // Filter keys if activeFilter is specified
  const paramKeys = Object.keys(customParams).filter((paramKey) => {
    if (!activeFilter || activeFilter === 'ALL') return true;
    const item = extractedParams?.[paramKey];
    const resolved = getResolvedStatus(item?.status);
    return resolved === activeFilter;
  });

  return (
    <div className="flex-1 flex flex-col gap-3">
      <div className="flex flex-col gap-0.5 text-left pb-1">
        <span className="text-xs font-bold text-[var(--text-main)]">
          Review Extracted Hyperparameters & Provenance Evidence
        </span>
        <span className="text-[9px] text-[var(--text-muted)] leading-tight">
          Every parameter includes its source section and extracted paper quote. Adjust values as needed before executing downstream synthesis.
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[360px] pr-1.5 scrollbar-thin flex flex-col gap-3 relative">
        <div className="grid grid-cols-2 gap-2 text-left">
          {paramKeys.map((paramKey) => {
            const item = extractedParams?.[paramKey];
            const label = paramKey.toUpperCase().replace('_', ' ');
            const resolvedStatus = getResolvedStatus(item?.status);
            const isTooltipOpen = activeTooltipParam === paramKey;

            return (
              <div
                key={paramKey}
                className={`relative border rounded-xl p-2.5 flex flex-col gap-2 transition-all ${getCardBorderStyles(
                  item?.status
                )}`}
              >
                {/* Header: Label, Status Badge & Info Tooltip Trigger */}
                <div className="flex justify-between items-center gap-1.5">
                  <span className="text-[9px] font-mono font-bold text-[var(--text-main)] truncate">
                    {label}
                  </span>

                  <div className="flex items-center gap-1 shrink-0">
                    <span
                      className={`text-[7px] font-mono px-1.5 py-0.5 rounded-md uppercase tracking-wider border leading-none ${getStatusBadgeStyles(
                        item?.status
                      )}`}
                    >
                      {resolvedStatus}
                    </span>

                    {/* Info Evidence Trigger */}
                    <button
                      type="button"
                      onClick={() =>
                        setActiveTooltipParam(isTooltipOpen ? null : paramKey)
                      }
                      className={`p-1 rounded-md transition-all cursor-pointer ${
                        isTooltipOpen
                          ? 'bg-[var(--accent)] text-white'
                          : 'text-[var(--text-muted)] hover:text-[var(--accent)] hover:bg-[var(--accent-subtle)]'
                      }`}
                      title="View paper provenance evidence"
                    >
                      <IconInfo2 className="text-xs" />
                    </button>
                  </div>
                </div>

                {/* Input Field */}
                <div className="relative">
                  <input
                    type="text"
                    value={customParams[paramKey] ?? ''}
                    onChange={(e) => handleFieldChange(paramKey, e.target.value)}
                    className="w-full bg-[var(--bg-card)] border app-border rounded-lg px-2.5 py-1 text-[var(--text-main)] font-mono text-[10px] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>

                {/* Paper Evidence Quote Drawer / Tooltip Popover */}
                {isTooltipOpen && (
                  <div className="mt-1 p-2.5 rounded-lg bg-[var(--bg-card)] border border-amber-500/40 shadow-xl flex flex-col gap-1.5 text-[9px] font-mono select-text z-20">
                    <div className="flex items-center justify-between border-b app-border pb-1">
                      <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                        <span className="font-bold text-[var(--text-main)]">
                          Provenance Evidence
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setActiveTooltipParam(null)}
                        className="text-[var(--text-muted)] hover:text-[var(--text-main)] cursor-pointer"
                      >
                        <IconClose className="text-xs" />
                      </button>
                    </div>

                    {/* Section Label */}
                    <div className="text-[9px] text-[var(--text-muted)]">
                      Source Section:{' '}
                      <strong className="text-[var(--text-main)]">
                        {item?.source_section || 'Section not explicitly specified'}
                      </strong>
                    </div>

                    {/* Paper-styled Blockquote */}
                    {item?.evidence_quote ? (
                      <blockquote className="p-2 rounded bg-amber-500/5 border-l-2 border-l-amber-400 font-serif italic text-[10px] text-[var(--text-main)] leading-relaxed">
                        “{item.evidence_quote}”
                      </blockquote>
                    ) : (
                      <div className="text-[8px] text-[var(--text-muted)] italic">
                        {resolvedStatus === 'DEFAULT'
                          ? 'No verbatim text quote in paper. Applied canonical ML baseline default.'
                          : 'Deduced via contextual architecture inference.'}
                      </div>
                    )}

                    {/* Confidence Score */}
                    {item?.confidence !== undefined && (
                      <div className="flex justify-between items-center pt-0.5 text-[8px] text-[var(--text-muted)]">
                        <span>Confidence:</span>
                        <span className="font-bold text-emerald-400">
                          {item.confidence}%
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {paramKeys.length === 0 && (
          <div className="py-8 flex flex-col items-center justify-center text-[var(--text-muted)] text-[10px] font-mono">
            <span>No parameters match the filter "{activeFilter}".</span>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 border-t app-border pt-2">
        <button
          type="button"
          onClick={onConfirm}
          className="text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2.5 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  );
};
