import React, { useState } from 'react';
import { parseInlineMarkdown } from '../../../utils/markdownParser';

interface ImplementationTabsProps {
  walkthroughContent: string;
  taskContent: string;
  isLoadingFiles: boolean;
}

export const ImplementationTabs: React.FC<ImplementationTabsProps> = ({
  walkthroughContent,
  taskContent,
  isLoadingFiles,
}) => {
  const [activeTab, setActiveTab] = useState<'walkthrough' | 'checklist'>('walkthrough');

  return (
    <div className="flex-1 flex flex-col gap-3">
      <div className="flex gap-2 border-b app-border pb-1.5">
        <button
          type="button"
          onClick={() => setActiveTab('walkthrough')}
          className={`text-[9px] font-mono font-bold px-3 py-1 rounded-lg transition-all cursor-pointer ${
            activeTab === 'walkthrough'
              ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
              : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
          }`}
        >
          Verification Walkthrough
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('checklist')}
          className={`text-[9px] font-mono font-bold px-3 py-1 rounded-lg transition-all cursor-pointer ${
            activeTab === 'checklist'
              ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
              : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
          }`}
        >
          Task Checklist
        </button>
      </div>

      <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[300px] flex flex-col gap-3">
        {isLoadingFiles ? (
          <div className="flex-1 flex items-center justify-center py-6">
            <div className="w-5 h-5 rounded-full border border-[var(--accent)] border-t-transparent animate-spin" />
          </div>
        ) : activeTab === 'walkthrough' ? (
          <div className="text-[10px] text-[var(--text-main)] leading-relaxed font-mono whitespace-pre-wrap select-text selection:bg-[var(--accent-subtle)] p-1 rounded">
            {walkthroughContent.split('\n').map((line, idx) => (
              <p key={idx} className="my-0.5">{parseInlineMarkdown(line)}</p>
            ))}
          </div>
        ) : (
          <div className="text-[10px] text-[var(--text-main)] leading-relaxed font-mono whitespace-pre-wrap select-text selection:bg-[var(--accent-subtle)] p-1 rounded">
            {taskContent.split('\n').map((line, idx) => (
              <p key={idx} className="my-0.5">{parseInlineMarkdown(line)}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
