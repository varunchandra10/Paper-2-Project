import React from 'react';
import { usePanelStore } from '../../../store/panelStore';

interface MilestoneItem {
  index: number;
  nodeKey: string;
  name: string;
  desc: string;
  isConditional?: boolean;
}

const MILESTONES: MilestoneItem[] = [
  { index: 0, nodeKey: 'ingestion_node', name: 'Step 1: Paper Ingestion', desc: 'Extract paper metadata, sections, and formulas' },
  { index: 1, nodeKey: 'extraction_node', name: 'Step 2: Method Decomposition', desc: 'Extract architecture, equations, and parameters' },
  { index: 2, nodeKey: 'feasibility_node', name: 'Step 3: Hardware Feasibility', desc: 'Compute memory footprint vs local hardware limits' },
  { index: 3, nodeKey: 'adaptation_node', name: 'Step 3b: Parameter Adaptation', desc: 'Constraint-aware parameter refinement loop', isConditional: true },
  { index: 4, nodeKey: 'sequencing_node', name: 'Step 4: Build Sequencing', desc: 'Topological DAG build ordering & dependencies' },
  { index: 5, nodeKey: 'specification_node', name: 'Step 4b: Architecture Spec', desc: 'Formal module signatures and architectural contracts' },
  { index: 6, nodeKey: 'code_generation_node', name: 'Step 5: Code Generation', desc: 'Dual-engine tournament LLM synthesis' },
  { index: 7, nodeKey: 'evaluation_node', name: 'Step 6: Code Verification', desc: '3-layer verification: syntax, runtime, paper fidelity' },
  { index: 8, nodeKey: 'repair_node', name: 'Step 6b: Auto-Repair (Reflexion)', desc: 'Iterative AST/runtime error self-healing', isConditional: true },
];

export const MilestoneTracker: React.FC = () => {
  const { milestoneStatuses, conditionalMilestonesVisible } = usePanelStore();

  const visibleMilestones = MILESTONES.filter((m) => {
    if (!m.isConditional) return true;
    const isVisible = conditionalMilestonesVisible?.[m.nodeKey] ||
      milestoneStatuses[m.index] === 'active' ||
      milestoneStatuses[m.index] === 'completed';
    return isVisible;
  });

  return (
    <div className="flex flex-col gap-2">
      {visibleMilestones.map((milestone) => {
        const status = milestoneStatuses[milestone.index] || 'pending';
        const isActive = status === 'active';
        const isCompleted = status === 'completed';

        return (
          <div
            key={milestone.nodeKey}
            className={`relative flex items-center p-2.5 rounded-lg border transition-all duration-300 ${
              isCompleted 
                ? 'border-emerald-500/30 bg-emerald-500/10 shadow-[0_0_8px_rgba(16,185,129,0.05)]' 
                : isActive 
                  ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-[0_0_12px_rgba(0,0,0,0.05)] ring-1 ring-[var(--accent)]/30' 
                  : 'border app-border bg-[var(--bg-base)] opacity-60'
            }`}
          >
            {/* Visual Indicator (Dot or Ring) */}
            <div className="mr-3 flex-shrink-0 relative">
              <div className={`h-3 w-3 rounded-full border transition-all duration-300 ${
                isCompleted 
                  ? 'bg-emerald-500 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' 
                  : isActive 
                    ? 'bg-[var(--accent)] border-[var(--accent)] animate-pulse shadow-[0_0_8px_rgba(0,0,0,0.2)]' 
                    : 'bg-transparent border-[var(--border-color)]'
              }`} />
            </div>

            {/* Content Details */}
            <div className="flex-1 flex flex-col font-sans pr-14">
              <div className="flex items-center gap-1.5">
                <span className={`text-[11px] font-bold tracking-tight ${
                  isCompleted 
                    ? 'text-emerald-500 line-through decoration-emerald-500/30' 
                    : isActive 
                      ? 'text-[var(--accent)] font-extrabold' 
                      : 'text-[var(--text-main)]'
                }`}>
                  {milestone.name}
                </span>
                {milestone.isConditional && (
                  <span className="text-[7.5px] uppercase font-mono px-1 py-0.2 bg-[var(--accent-subtle)] text-[var(--accent)] rounded border border-[var(--accent-border)] font-bold">
                    Loop
                  </span>
                )}
              </div>
              <span className="text-[8.5px] text-[var(--text-muted)] mt-0.5 leading-normal line-clamp-1">
                {milestone.desc}
              </span>
            </div>

            {/* Status Stamp Overlay */}
            {isCompleted && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 border-2 border-emerald-500/60 text-emerald-500 text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded rotate-6 select-none pointer-events-none opacity-80 shadow-sm">
                PASSED
              </div>
            )}
            {isActive && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 border border-[var(--accent)] text-[var(--accent)] text-[7px] font-mono uppercase tracking-widest font-extrabold px-1.5 py-0.5 rounded animate-pulse select-none pointer-events-none opacity-90 shadow-sm">
                ACTIVE
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
