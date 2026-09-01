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
                ? 'border-confirmed/30 bg-confirmed/5' 
                : isActive 
                  ? 'border-brass bg-brass/5 shadow-[0_0_12px_rgba(201,154,62,0.1)]' 
                  : 'border-border bg-muted/20 opacity-55'
            }`}
          >
            {/* Visual Indicator (Dot or Ring) */}
            <div className="mr-3.5 flex-shrink-0 relative">
              <div className={`h-3 w-3 rounded-full border transition-all duration-300 ${
                isCompleted 
                  ? 'bg-confirmed border-confirmed shadow-[0_0_8px_rgba(107,155,124,0.4)]' 
                  : isActive 
                    ? 'bg-brass border-brass animate-pulse shadow-[0_0_8px_rgba(201,154,62,0.5)]' 
                    : 'bg-transparent border-border'
              }`} />
            </div>

            {/* Content Details */}
            <div className="flex-1 flex flex-col">
              <span className={`text-[11px] font-bold tracking-tight font-serif ${
                isCompleted 
                  ? 'text-confirmed line-through decoration-confirmed/30' 
                  : isActive 
                    ? 'text-brass font-extrabold' 
                    : 'text-foreground/75'
              }`}>
                {milestone.name}
              </span>
              <span className="text-[8px] text-muted-foreground mt-0.5 leading-normal">
                {milestone.desc}
              </span>
            </div>

            {/* Vintage Library Ink Stamp overlay */}
            {isCompleted && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 border-2 border-confirmed/50 text-confirmed text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded rotate-12 select-none pointer-events-none scale-110 opacity-70">
                PASSED
              </div>
            )}
            {isActive && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 border border-brass/50 text-brass text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded animate-pulse select-none pointer-events-none opacity-60">
                ACTIVE
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
