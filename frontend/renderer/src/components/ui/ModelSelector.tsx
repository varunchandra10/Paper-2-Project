import React, { useState, useRef, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaRobot, FaCode, FaBrain } from 'react-icons/fa6';
import { FiChevronUp, FiCheck } from 'react-icons/fi';

interface ModelOption {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
}

const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'gpt-oss-120b',
    name: 'GPT-OSS 120B',
    description: 'Main reasoning + architecture + difficult code',
    icon: <FaBrain className="text-brass text-xs shrink-0" />
  },
  {
    id: 'qwen3-coder-480b',
    name: 'Qwen3 Coder 480B',
    description: 'Code generation / repository-level coding',
    icon: <FaCode className="text-brass text-xs shrink-0" />
  },
  {
    id: 'qwen3-next-80b',
    name: 'Qwen3 Next 80B',
    description: 'General paper understanding + RAG',
    icon: <FaRobot className="text-brass text-xs shrink-0" />
  },
  {
    id: 'deepseek-r1',
    name: 'DeepSeek R1',
    description: 'Deep reasoning / verification',
    icon: <FaBrain className="text-brass text-xs shrink-0" />
  },
  {
    id: 'qwen3.6-27b',
    name: 'Qwen 3.6 27B',
    description: 'Vision + equations/figures + extraction assistance',
    icon: <FaRobot className="text-brass text-xs shrink-0" />
  }
];

export const ModelSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { selectedModel, setSelectedModel } = usePanelStore();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeOption = MODEL_OPTIONS.find(opt => opt.id === selectedModel) || MODEL_OPTIONS[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative font-mono" ref={dropdownRef}>
      {/* Dropdown Toggle Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl border border-border/50 bg-card/80 hover:bg-muted/50 text-[11px] text-foreground outline-none hover:border-brass/40 transition-all duration-200 shadow-sm cursor-pointer select-none active:scale-[0.98]"
        title="Select Active LLM Engine"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {activeOption.icon}
          <span className="font-semibold text-foreground/90 truncate max-w-[120px]">
            {activeOption.name}
          </span>
        </div>
        <FiChevronUp 
          className={`text-xs text-muted-foreground/70 transition-transform duration-200 shrink-0 ${
            isOpen ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {/* Floating Dropdown Option List */}
      {isOpen && (
        <div 
          className="absolute bottom-[calc(100%+8px)] left-0 w-[260px] max-w-[calc(100vw-32px)] bg-card border border-border/70 rounded-2xl shadow-2xl z-50 p-1.5 flex flex-col gap-1 select-none animate-fade-in"
          role="listbox"
        >
          {/* Menu Header */}
          <div className="px-2.5 py-1.5 text-[9px] font-mono font-bold text-brass/80 uppercase tracking-wider border-b border-border/30">
            Select Pipeline Model
          </div>

          {/* Model Options List */}
          <div className="flex flex-col gap-0.5 max-h-[220px] overflow-y-auto scrollbar-thin scrollbar-thumb-border/40 scrollbar-track-transparent">
            {MODEL_OPTIONS.map((option) => {
              const isSelected = selectedModel === option.id;
              return (
                <div
                  key={option.id}
                  onClick={() => {
                    setSelectedModel(option.id);
                    setIsOpen(false);
                  }}
                  className={`flex items-start gap-2.5 p-2 rounded-xl transition-all duration-150 cursor-pointer group ${
                    isSelected
                      ? 'bg-brass/10 border border-brass/30 text-foreground'
                      : 'border border-transparent hover:bg-muted/50 text-muted-foreground hover:text-foreground'
                  }`}
                  role="option"
                  aria-selected={isSelected}
                >
                  <div className="mt-0.5 p-1 rounded-lg bg-background/50 border border-border/30 shrink-0 group-hover:border-brass/30 transition-colors">
                    {option.icon}
                  </div>
                  
                  <div className="flex flex-col flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className={`text-[11px] font-bold truncate ${isSelected ? 'text-brass' : 'text-foreground'}`}>
                        {option.name}
                      </span>
                      {isSelected && (
                        <FiCheck className="text-brass text-xs shrink-0" />
                      )}
                    </div>
                    <span className="text-[9px] text-muted-foreground leading-relaxed truncate font-sans">
                      {option.description}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};