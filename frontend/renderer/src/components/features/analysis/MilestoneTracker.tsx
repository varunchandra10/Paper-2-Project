import React from 'react';
import { usePanelStore } from '../../../store/panelStore';

export const MilestoneTracker: React.FC = () => {
  const { milestoneStatuses } = usePanelStore();

  const milestones = [
    { name: '1. Paper Ingestion', desc: 'Extract paper metadata and contributions' },
    { name: '2. Method Decomposition', desc: 'Segment method components and hyperparams' },
    { name: '3. Parameters Refinement', desc: 'Search Tavily/GitHub for missing gaps' },
    { name: '4. Hardware Feasibility', desc: 'Validate memory footprint on local VRAM' },
    { name: '5. Blueprint Synthesis', desc: 'Sequence implementation and print proposal' }
  ];

  return (
    <div className="flex flex-col gap-2.5">
      {milestones.map((milestone, idx) => {
        const status = milestoneStatuses[idx];
        const isActive = status === 'active';
        const isCompleted = status === 'completed';

        return (
          <div
            key={idx}
            className={`relative flex items-center p-3 rounded-lg border transition-all duration-300 ${
              isCompleted 
                ? 'border-emerald-500/30 bg-emerald-500/10' 
                : isActive 
                  ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-[0_0_12px_rgba(0,0,0,0.05)]' 
                  : 'border app-border bg-[var(--bg-base)] opacity-60'
            }`}
          >
            {/* Visual Indicator (Dot or Ring) */}
            <div className="mr-3.5 flex-shrink-0 relative">
              <div className={`h-3 w-3 rounded-full border transition-all duration-300 ${
                isCompleted 
                  ? 'bg-emerald-500 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' 
                  : isActive 
                    ? 'bg-[var(--accent)] border-[var(--accent)] animate-pulse shadow-[0_0_8px_rgba(0,0,0,0.2)]' 
                    : 'bg-transparent border-[var(--border-color)]'
              }`} />
            </div>

            {/* Content Details */}
            <div className="flex-1 flex flex-col font-sans">
              <span className={`text-[11px] font-bold tracking-tight ${
                isCompleted 
                  ? 'text-emerald-500 line-through decoration-emerald-500/30' 
                  : isActive 
                    ? 'text-[var(--accent)] font-extrabold' 
                    : 'text-[var(--text-main)]'
              }`}>
                {milestone.name}
              </span>
              <span className="text-[8px] text-[var(--text-muted)] mt-0.5 leading-normal">
                {milestone.desc}
              </span>
            </div>

            {/* Vintage Ink Stamp overlay */}
            {isCompleted && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 border-2 border-emerald-500/50 text-emerald-500 text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded rotate-12 select-none pointer-events-none scale-110 opacity-70">
                PASSED
              </div>
            )}
            {isActive && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 border border-[var(--accent-border)] text-[var(--accent)] text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded animate-pulse select-none pointer-events-none opacity-80">
                ACTIVE
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
