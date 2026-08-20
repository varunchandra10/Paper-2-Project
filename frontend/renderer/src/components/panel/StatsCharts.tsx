import React from 'react';
import { usePanelStore } from '../../store/panelStore';

export const StatsCharts: React.FC = () => {
  const { activeMilestoneIndex, milestoneStatuses, decompScore, paramCertainty } = usePanelStore();

  const getProgressPercent = () => {
    if (activeMilestoneIndex === -1) return 0;
    const completed = milestoneStatuses.filter((s) => s === 'completed').length;
    if (completed === 5) return 100;
    const active = milestoneStatuses.filter((s) => s === 'active').length;
    return completed * 20 + (active ? 10 : 0);
  };

  const progress = getProgressPercent();
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="flex items-center gap-5 bg-black/15 border border-border rounded-xl p-4 shadow-inner">
      {/* SVG Circular Ring */}
      <div className="relative w-20 h-20 flex-shrink-0">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
          <circle 
            className="text-border" 
            strokeWidth="5" 
            stroke="currentColor" 
            fill="transparent" 
            r={radius} 
            cx="40" 
            cy="40" 
          />
          <circle 
            className="text-brass transition-all duration-700 ease-out" 
            strokeWidth="5" 
            strokeDasharray={circumference} 
            strokeDashoffset={strokeDashoffset} 
            strokeLinecap="round" 
            stroke="currentColor" 
            fill="transparent" 
            r={radius} 
            cx="40" 
            cy="40" 
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-[14px] font-mono font-extrabold tracking-tighter leading-none">{progress}%</span>
          <span className="text-[6.5px] uppercase font-bold tracking-wider text-muted-foreground mt-0.5">Ingested</span>
        </div>
      </div>

      {/* Linear metrics bars */}
      <div className="flex-1 flex flex-col gap-3">
        {/* Metric 1 */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-[10px] font-bold">
            <span className="text-foreground/60">Decomposition Score</span>
            <span className="text-brass font-mono">{decompScore}%</span>
          </div>
          <div className="w-full h-1.5 bg-black/20 rounded-full overflow-hidden">
            <div 
              className="h-full bg-brass rounded-full shadow-[0_0_6px_rgba(201,154,62,0.3)] transition-all duration-700 ease-out"
              style={{ width: `${decompScore}%` }}
            />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-[10px] font-bold">
            <span className="text-foreground/60">Param Certainty</span>
            <span className="text-brass font-mono">{paramCertainty}%</span>
          </div>
          <div className="w-full h-1.5 bg-black/20 rounded-full overflow-hidden">
            <div 
              className="h-full bg-brass rounded-full shadow-[0_0_6px_rgba(201,154,62,0.3)] transition-all duration-700 ease-out"
              style={{ width: `${paramCertainty}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
