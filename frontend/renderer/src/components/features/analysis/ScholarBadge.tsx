import React from 'react';

export interface ScholarMetadata {
  tldr?: string;
  citations?: number;
}

interface ScholarBadgeProps {
  metadata: ScholarMetadata | null;
}

export const ScholarBadge: React.FC<ScholarBadgeProps> = ({ metadata }) => {
  if (!metadata || (!metadata.tldr && metadata.citations === undefined)) {
    return null;
  }

  return (
    <div className="bg-[var(--accent-subtle)] border border-[var(--accent-border)] rounded-lg p-2.5 flex flex-col gap-1 text-left text-[10px] my-1">
      <div className="flex justify-between items-center">
        <span className="font-mono font-bold text-[var(--accent)] uppercase text-[9px]">
          Academic Reception (Semantic Scholar)
        </span>
        {metadata.citations !== undefined && (
          <span className="bg-[var(--accent-subtle)] text-[var(--accent)] font-mono text-[8px] px-2 py-0.5 rounded-full border border-[var(--accent-border)]">
            {metadata.citations} Citations
          </span>
        )}
      </div>
      {metadata.tldr && (
        <p className="text-[var(--text-main)] font-sans text-[10px] italic leading-tight">
          "{metadata.tldr}"
        </p>
      )}
    </div>
  );
};
