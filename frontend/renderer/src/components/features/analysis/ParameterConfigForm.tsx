import React from 'react';

interface ExtractedParamMeta {
  value: string;
  status: string;
  confidence: number;
}

interface ParameterConfigFormProps {
  customParams: Record<string, string>;
  extractedParams?: Record<string, ExtractedParamMeta> | null;
  onChange: (params: Record<string, string>) => void;
  onConfirm: () => void;
  confirmLabel?: string;
  compactMode?: boolean;
}

export const ParameterConfigForm: React.FC<ParameterConfigFormProps> = ({
  customParams,
  extractedParams,
  onChange,
  onConfirm,
  confirmLabel = 'Confirm & Run Feasibility Check',
  compactMode = false,
}) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'EXPLICIT':
        return 'border-emerald-500/25 bg-emerald-500/5 text-emerald-400';
      case 'INFERRED':
      case 'DERIVED':
        return 'border-sky-500/25 bg-sky-500/5 text-sky-400';
      case 'ASSUMED':
        return 'border-amber-500/25 bg-amber-500/5 text-amber-400';
      case 'UNKNOWN':
        return 'border-rose-500/25 bg-rose-500/5 text-rose-400';
      default:
        return 'border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-muted)]';
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
          {compactKeys.map((key) => (
            <div key={key} className="flex flex-col gap-1">
              <label className="text-[8px] font-mono text-[var(--text-muted)] capitalize">
                {key.replace('_', ' ')}
              </label>
              <input
                type="text"
                value={customParams[key] || ''}
                onChange={(e) => handleFieldChange(key, e.target.value)}
                className="bg-[var(--bg-card)] border app-border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          ))}
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

  return (
    <div className="flex-1 flex flex-col gap-3">
      <div className="flex flex-col gap-0.5 text-left pb-1">
        <span className="text-xs font-bold text-[var(--text-main)]">
          Review Extracted Hyperparameters
        </span>
        <span className="text-[9px] text-[var(--text-muted)] leading-tight">
          Review or adjust target attributes before executing the hardware resource compatibility analysis.
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[360px] pr-1.5 scrollbar-thin flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2 text-left">
          {Object.keys(customParams).map((paramKey) => {
            const item = extractedParams?.[paramKey];
            const label = paramKey.toUpperCase().replace('_', ' ');

            return (
              <div
                key={paramKey}
                className="bg-[var(--bg-base)]/50 border app-border rounded-lg p-2 flex flex-col gap-1.5 transition-all"
              >
                <div className="flex justify-between items-center gap-1.5">
                  <span className="text-[8px] font-mono font-bold text-[var(--accent)]">
                    {label}
                  </span>
                  {item && (
                    <span
                      className={`text-[7px] font-mono font-semibold border px-1.5 py-0.2 rounded-full leading-none uppercase ${getStatusColor(
                        item.status
                      )}`}
                    >
                      {item.status}
                    </span>
                  )}
                </div>
                <input
                  type="text"
                  value={customParams[paramKey]}
                  onChange={(e) => handleFieldChange(paramKey, e.target.value)}
                  className="w-full bg-[var(--bg-card)] border app-border rounded px-2.5 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                />
              </div>
            );
          })}
        </div>
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
