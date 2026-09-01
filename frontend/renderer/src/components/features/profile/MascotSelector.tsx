import React from 'react';
import { FiCheck } from 'react-icons/fi';
import mrNerdyStandSleep from '../../../assets/mr_nerdy_stand_sleep-removebg-preview.png';

export interface MascotOption {
  id: string;
  name: string;
  description: string;
  emoji: string;
}

export const MASCOT_OPTIONS: MascotOption[] = [
  {
    id: 'mr-nerdy',
    name: 'Mr. Nerdy',
    description: 'The Default Academic Companion. Enthusiastic about RAG and equations.',
    emoji: '🤓'
  },
  {
    id: 'aether-scholar',
    name: 'Aether Scholar',
    description: 'The Analytical Code Wizard. Expert in multi-agent compiler steps.',
    emoji: '🧙‍♂️'
  },
  {
    id: 'synthexis-bot',
    name: 'Synthexis Bot',
    description: 'The Automated Execution Engine. Focuses strictly on pipeline code output.',
    emoji: '🤖'
  }
];

interface MascotSelectorProps {
  formAvatar: string;
  setFormAvatar: (id: string) => void;
}

export const MascotSelector: React.FC<MascotSelectorProps> = ({
  formAvatar,
  setFormAvatar
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {MASCOT_OPTIONS.map((mascot) => {
        const isSelected = formAvatar === mascot.id;
        return (
          <div
            key={mascot.id}
            onClick={() => setFormAvatar(mascot.id)}
            className={`group rounded-2xl border p-3.5 flex flex-col items-center text-center gap-2.5 transition-all duration-200 cursor-pointer select-none overflow-hidden relative ${
              isSelected
                ? 'border-[var(--accent-border)] bg-[var(--accent-subtle)] shadow-xs ring-1 ring-[var(--accent)]'
                : 'border app-border bg-[var(--bg-base)]/50 hover:bg-[var(--accent-subtle)] hover:border-[var(--accent-border)]'
            }`}
          >
            <div className="w-14 h-14 rounded-2xl bg-[var(--bg-base)] border app-border flex items-center justify-center text-2xl relative shadow-inner group-hover:scale-105 transition-transform duration-200">
              {mascot.id === 'mr-nerdy' ? (
                <img 
                  src={mrNerdyStandSleep} 
                  alt="Mr. Nerdy Face" 
                  className="h-11 w-auto object-contain translate-y-0.5" 
                />
              ) : (
                <span>{mascot.emoji}</span>
              )}
              
              {isSelected && (
                <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-[var(--accent)] text-white rounded-full flex items-center justify-center text-[10px] font-black border-2 border-[var(--bg-base)] shadow-xs">
                  <FiCheck className="stroke-[3]" />
                </span>
              )}
            </div>

            <div className="flex flex-col min-w-0">
              <span className={`text-xs font-bold leading-tight ${isSelected ? 'text-[var(--accent)]' : 'text-[var(--text-main)]'}`}>
                {mascot.name}
              </span>
              <span className="text-[9.5px] text-[var(--text-muted)] mt-1 leading-relaxed font-sans">
                {mascot.description}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
