import React, { useState } from 'react';
import { parseInlineMarkdown } from './messageFormatters';

export const ReActStepsAccordion: React.FC<{
  thought?: string;
  action?: string;
  observation?: string;
}> = ({ thought, action, observation }) => {
  const [isOpen, setIsOpen] = useState(false);

  const stepCount = [thought, action, observation].filter(Boolean).length || 1;

  const renderCleanedContent = (text?: string) => {
    if (!text) return null;
    const lines = text.split('\n')
      .map(line => line.trim())
      .filter(line => line !== '**' && line !== '');

    return lines.map((line, idx) => (
      <div key={idx} className="min-h-[1.25em]">
        {parseInlineMarkdown(line)}
      </div>
    ));
  };

  return (
    <div className="w-full flex flex-col items-start select-none mb-1.5">
      {/* ── Themed ReACT Trigger Pill Badge ── */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg border app-border bg-[var(--bg-card)]/90 hover:bg-[var(--bg-card)] hover:border-[var(--accent)]/50 backdrop-blur-md shadow-xs transition-all duration-200 cursor-pointer group"
        title="Toggle ReACT reasoning steps"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.6)] animate-pulse shrink-0" />
        <span className="font-mono text-[10px] font-bold tracking-wider uppercase text-[var(--text-main)] group-hover:text-[var(--accent)] transition-colors">
          ReACT Reasoning Trace
        </span>
        <span className="px-1.5 py-0.5 rounded text-[8.5px] font-mono font-semibold bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] leading-none">
          {stepCount} {stepCount === 1 ? 'step' : 'steps'}
        </span>
        <svg 
          className={`w-3 h-3 text-[var(--text-muted)] transition-transform duration-200 group-hover:text-[var(--text-main)] ${
            isOpen ? 'rotate-180 text-[var(--accent)]' : ''
          }`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/>
        </svg>
      </button>

      {/* ── Expandable Panel Container with Fixed Max Height & Scrollbar ── */}
      <div
        className={`w-full transition-all duration-300 ease-in-out overflow-x-hidden ${
          isOpen ? 'max-h-[320px] opacity-100 mt-1.5 mb-1' : 'max-h-0 opacity-0 pointer-events-none overflow-hidden'
        }`}
      >
        <div className="border app-border rounded-xl p-3 max-h-[280px] overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent space-y-2.5 text-xs font-mono shadow-sm bg-[var(--bg-base)]/90 backdrop-blur-md pr-2 w-full max-w-full">
          {/* Step Badges Row (Sticky at top when scrolling trace) */}
          <div className="sticky -top-3 -mx-3 px-3 pt-1 pb-2 bg-[var(--bg-base)]/95 backdrop-blur-md flex items-center justify-between gap-1.5 border-b app-border text-[9px] font-mono z-10">
            <div className="flex items-center gap-1.5 flex-wrap">
              {thought && (
                <span className="px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-500/30 text-[var(--warning-fg)] font-bold uppercase tracking-wider">
                  Thought
                </span>
              )}
              {thought && action && <span className="text-[var(--text-muted)] text-[10px]">➔</span>}
              {action && (
                <span className="px-2 py-0.5 rounded-md bg-sky-400/15 border border-sky-400/30 text-sky-400 font-bold uppercase tracking-wider">
                  Action
                </span>
              )}
              {action && observation && <span className="text-[var(--text-muted)] text-[10px]">➔</span>}
              {observation && (
                <span className="px-2 py-0.5 rounded-md bg-emerald-400/15 border border-emerald-400/30 text-emerald-400 font-bold uppercase tracking-wider">
                  Observation
                </span>
              )}
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono select-none">
              scrollable
            </span>
          </div>

          {/* Detailed Content — Stacked Vertically */}
          {thought && (
            <div className="flex flex-col gap-1.5 min-w-0 w-full">
              <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-amber-500/15 text-[var(--warning-fg)] border border-amber-500/30 w-fit select-none">
                Thought
              </span>
              <div className="text-[var(--text-main)]/90 text-[11px] leading-relaxed whitespace-pre-wrap break-words break-all pl-0.5">
                {renderCleanedContent(thought)}
              </div>
            </div>
          )}

          {action && (
            <div className="flex flex-col gap-1.5 min-w-0 w-full pt-2 border-t app-border/60">
              <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-sky-400/15 text-sky-400 border border-sky-400/30 w-fit select-none">
                Action
              </span>
              <div className="text-[var(--text-main)]/90 text-[11px] leading-relaxed whitespace-pre-wrap break-words break-all pl-0.5">
                {renderCleanedContent(action)}
              </div>
            </div>
          )}

          {observation && (
            <div className="flex flex-col gap-1.5 min-w-0 w-full pt-2 border-t app-border/60">
              <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-emerald-400/15 text-emerald-400 border border-emerald-400/30 w-fit select-none">
                Observation
              </span>
              <div className="text-[var(--text-main)]/90 text-[11px] leading-relaxed whitespace-pre-wrap break-words break-all pl-0.5">
                {renderCleanedContent(observation)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
