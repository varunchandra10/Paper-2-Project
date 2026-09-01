import React from 'react';
import { usePanelStore } from '../../store/panelStore';

export const TierSelector: React.FC = () => {
  const { selectedTier, setSelectedTier } = usePanelStore();

  const tiers = [
    { id: 'brief', name: 'Brief', desc: 'Summary metrics' },
    { id: 'detailed', name: 'Detailed', desc: 'Hyperparams & logic' },
    { id: 'implement', name: 'Implement', desc: 'Scaffold code blueprint' }
  ] as const;

  return (
    <div className="flex bg-muted/40 border border-border rounded-lg p-0.5" role="radiogroup" aria-label="Select blueprint depth">
      {tiers.map((tier) => (
        <button
          key={tier.id}
          onClick={() => setSelectedTier(tier.id)}
          className={`flex-1 py-1.5 px-2 rounded-md text-[10px] font-bold transition-all duration-200 cursor-pointer flex flex-col items-center ${
            selectedTier === tier.id
              ? 'bg-brass text-ink font-extrabold shadow'
              : 'text-foreground/50 hover:text-foreground hover:bg-foreground/5'
          }`}
          role="radio"
          aria-checked={selectedTier === tier.id}
        >
          <span>{tier.name}</span>
          <span className={`text-[7px] font-normal leading-none mt-0.5 ${
            selectedTier === tier.id ? 'text-ink/70' : 'text-foreground/30'
          }`}>{tier.desc}</span>
        </button>
      ))}
    </div>
  );
};
