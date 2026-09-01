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
    <div className="mb-3 w-full flex flex-col items-start gap-1 select-none">
      {/* ── Trigger Row matching exact mockup screenshot ── */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-[11px] font-mono text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors cursor-pointer group py-1 px-0"
        title="Toggle ReACT reasoning steps"
      >
        <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
        <span className="font-semibold tracking-wide uppercase text-[10.5px] text-[var(--text-main)] group-hover:text-[var(--accent)] transition-colors">
          REACT REASONING TRACE
        </span>
        <svg 
          className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180 text-[var(--accent)]' : 'text-[var(--text-muted)]'}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/>
        </svg>
        <span className="text-[10px] text-[var(--text-muted)] opacity-70 group-hover:opacity-100 transition-opacity">
          {stepCount} {stepCount === 1 ? 'step' : 'steps'}
        </span>
      </button>

      {/* ── Expandable Panel Container ── */}
      <div
        className={`w-full overflow-hidden transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-[800px] opacity-100 mt-1' : 'max-h-0 opacity-0 pointer-events-none'
        }`}
      >
        <div 
          className="border app-border rounded-xl p-3.5 space-y-2.5 text-xs font-mono shadow-sm"
          style={{ backgroundColor: 'var(--code-bg)' }}
        >
          {/* Step Badges Row */}
          <div className="flex items-center gap-1.5 pb-2 border-b app-border text-[9px] font-mono">
            {thought && (
              <span className="px-2 py-0.5 rounded bg-amber-400/15 border border-amber-400/30 text-amber-400 font-bold uppercase tracking-wider">
                Thought
              </span>
            )}
            {thought && action && <span className="text-[var(--text-muted)]">➔</span>}
            {action && (
              <span className="px-2 py-0.5 rounded bg-sky-400/15 border border-sky-400/30 text-sky-400 font-bold uppercase tracking-wider">
                Action
              </span>
            )}
            {action && observation && <span className="text-[var(--text-muted)]">➔</span>}
            {observation && (
              <span className="px-2 py-0.5 rounded bg-emerald-400/15 border border-emerald-400/30 text-emerald-400 font-bold uppercase tracking-wider">
                Observation
              </span>
            )}
          </div>

          {/* Detailed Content */}
          {thought && (
            <div className="flex items-start gap-2.5">
              <span className="mt-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-amber-400/15 text-amber-400 shrink-0">
                Thought
              </span>
              <div className="text-[var(--text-muted)] leading-relaxed whitespace-pre-wrap flex-1">
                {renderCleanedContent(thought)}
              </div>
            </div>
          )}

          {action && (
            <div className="flex items-start gap-2.5">
              <span className="mt-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-sky-400/15 text-sky-400 shrink-0">
                Action
              </span>
              <div className="text-[var(--text-muted)] leading-relaxed whitespace-pre-wrap flex-1">
                {renderCleanedContent(action)}
              </div>
            </div>
          )}

          {observation && (
            <div className="flex items-start gap-2.5">
              <span className="mt-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-emerald-400/15 text-emerald-400 shrink-0">
                Observation
              </span>
              <div className="text-[var(--text-muted)] leading-relaxed whitespace-pre-wrap flex-1">
                {renderCleanedContent(observation)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
