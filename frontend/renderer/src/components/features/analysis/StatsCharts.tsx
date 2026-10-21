import React from 'react';
import { usePanelStore } from '../../../store/panelStore';

export const StatsCharts: React.FC = () => {
  const { pipelineProgress, currentNodeLabel, isAnalyzing, analysisStatus } = usePanelStore();

  const progress = Math.min(100, Math.max(0, Math.round(pipelineProgress || 0)));
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const getStatusLabel = () => {
    if (analysisStatus === 'error') return 'Failed';
    if (isAnalyzing) return 'Running';
    if (progress === 100 || analysisStatus === 'success') return 'Complete';
    if (analysisStatus === 'paused_for_review') return 'Paused';
    return 'Idle';
  };

  const getStageText = () => {
    if (currentNodeLabel) return currentNodeLabel;
    if (isAnalyzing) return 'Pipeline Active...';
    if (progress === 100 || analysisStatus === 'success') return 'Synthesis Complete';
    if (analysisStatus === 'paused_for_review') return 'Waiting for Approval';
    if (analysisStatus === 'error') return 'Execution Halted';
    return 'Ready for Ingestion';
  };

  return (
    <div className="flex items-center gap-5 bg-[var(--bg-card)] border app-border rounded-xl p-4 shadow-inner text-[var(--text-main)]">
      {/* SVG Circular Ring */}
      <div className="relative w-20 h-20 flex-shrink-0">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
          <circle 
            className="text-[var(--border-color)]" 
            strokeWidth="5" 
            stroke="currentColor" 
            fill="transparent" 
            r={radius} 
            cx="40" 
            cy="40" 
          />
          <circle 
            className={`transition-all duration-700 ease-out ${
              progress === 100 ? 'text-emerald-500' : 'text-[var(--accent)]'
            }`}
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
          <span className="text-[14px] font-mono font-extrabold tracking-tighter leading-none text-[var(--text-main)]">
            {progress}%
          </span>
          <span className="text-[6.5px] uppercase font-bold tracking-wider text-[var(--text-muted)] mt-1">
            {getStatusLabel()}
          </span>
        </div>
      </div>

      {/* Linear metrics & active stage bars */}
      <div className="flex-1 flex flex-col gap-3">
        {/* Real Pipeline Progress Bar */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-[10px] font-bold">
            <span className="text-[var(--text-muted)]">Pipeline Progress</span>
            <span className={`font-mono ${progress === 100 ? 'text-emerald-500' : 'text-[var(--accent)]'}`}>
              {progress}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-[var(--bg-base)] rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                progress === 100 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-[var(--accent)]'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Current Node / Execution Stage */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-[10px] font-bold">
            <span className="text-[var(--text-muted)]">Current Stage</span>
            <span className={`font-mono text-[9px] px-1.5 py-0.5 rounded border max-w-[150px] truncate ${
              isAnalyzing 
                ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent-border)] animate-pulse' 
                : (progress === 100 
                  ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' 
                  : 'bg-[var(--bg-base)] text-[var(--text-muted)] border-[var(--border-color)]')
            }`}>
              {getStageText()}
            </span>
          </div>
          <div className="w-full h-1.5 bg-[var(--bg-base)] rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                isAnalyzing 
                  ? 'bg-gradient-to-r from-[var(--accent)] to-emerald-400 animate-pulse' 
                  : (progress === 100 ? 'bg-emerald-500' : 'bg-[var(--border-color)]')
              }`}
              style={{ width: `${Math.max(15, progress)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
