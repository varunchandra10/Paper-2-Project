import React, { useState, useRef, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { API_BASE } from '../../store/utils/storeUtils';
import { SkinLoader } from './SkinLoader';
import { IconRobot, IconCode, IconBrain, IconUp, IconCheck, IconCpu } from './Icons';

interface ModelOption {
  id: string;
  name: string;
  tag: string;
  description: string;
  icon: React.ReactNode;
}

const FALLBACK_MODELS: ModelOption[] = [
  {
    id: 'llama-3.3-70b',
    name: 'Llama 3.3 70B',
    tag: 'CLOUD',
    description: 'Main reasoning & paper Q&A synthesis (Groq / OpenRouter)',
    icon: <IconBrain className="text-[var(--accent)] text-xs shrink-0" />
  },
  {
    id: 'qwen-2.5-coder-32b',
    name: 'Qwen 2.5 Coder 32B',
    tag: 'CLOUD',
    description: 'Code extraction, schema generation & LaTeX formulas',
    icon: <IconCode className="text-[var(--accent)] text-xs shrink-0" />
  },
  {
    id: 'deepseek-r1-distill',
    name: 'DeepSeek R1 Distill',
    tag: 'CLOUD',
    description: 'Advanced logical step-by-step chain-of-thought analysis',
    icon: <IconRobot className="text-[var(--accent)] text-xs shrink-0" />
  },
  {
    id: 'gemini-2.0-flash',
    name: 'Gemini 2.0 Flash',
    tag: 'LONG CTX',
    description: 'Long-document RAG & fast paper processing',
    icon: <IconRobot className="text-[var(--accent)] text-xs shrink-0" />
  },
  {
    id: 'qwen2.5-coder:1.5b',
    name: 'Qwen 2.5 Coder 1.5B',
    tag: 'LOCAL',
    description: 'Offline Ollama local fallback engine',
    icon: <IconCpu className="text-[var(--accent)] text-xs shrink-0" />
  }
];

export const ModelSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [models, setModels] = useState<ModelOption[]>(FALLBACK_MODELS);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const { selectedModel, setSelectedModel } = usePanelStore();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeOption = models.find(opt => opt.id === selectedModel) || models[0] || FALLBACK_MODELS[0];

  useEffect(() => {
    let isMounted = true;
    const fetchModels = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`${API_BASE}/models`);
        if (res.ok) {
          const data = await res.json();
          const apiModels = data.models || [];
          if (apiModels.length > 0 && isMounted) {
            const mapped: ModelOption[] = apiModels.map((m: any) => ({
              id: m.id,
              name: m.name,
              tag: m.tag || 'MODEL',
              description: m.description || '',
              icon: m.tag === 'LOCAL' ? <IconCpu className="text-[var(--accent)] text-xs shrink-0" />
                  : m.tag === 'CODE' ? <IconCode className="text-[var(--accent)] text-xs shrink-0" />
                  : m.tag === 'LONG CTX' ? <IconRobot className="text-[var(--accent)] text-xs shrink-0" />
                  : <IconBrain className="text-[var(--accent)] text-xs shrink-0" />
            }));
            setModels(mapped);
          }
        }
      } catch (err) {
        console.error("Failed to fetch dynamic inference models:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchModels();
    return () => { isMounted = false; };
  }, []);

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
    <div className="relative font-mono select-none" ref={dropdownRef}>
      {/* Dropdown Toggle Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between gap-1.5 px-2.5 py-1 rounded-lg border transition-all duration-200 text-[11px] font-mono outline-none cursor-pointer active:scale-[0.98] ${
          isOpen 
            ? 'border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--text-main)] shadow-xs' 
            : 'border-[var(--border-color)] bg-[var(--bg-base)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
        }`}
        title="Select Active Inference Engine"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="shrink-0 text-[var(--accent)] text-xs">
            {activeOption.icon}
          </div>
          <span className="font-semibold text-[11px] text-[var(--text-main)] truncate max-w-[130px] leading-none">
            {activeOption.name}
          </span>
          <span className="text-[9px] text-[var(--accent)] font-mono font-semibold">
            [{activeOption.tag}]
          </span>
        </div>
        <IconUp 
          className={`text-xs text-[var(--text-muted)] transition-transform duration-200 shrink-0 ml-1 ${
            isOpen ? 'rotate-180 text-[var(--accent)]' : ''
          }`} 
        />
      </button>

      {/* Floating Dropdown Option List */}
      {isOpen && (
        <div 
          className="absolute bottom-[calc(100%+8px)] left-0 w-[280px] max-w-[calc(100vw-32px)] bg-[var(--bg-card)] border app-border rounded-2xl shadow-[0_12px_32px_rgba(0,0,0,0.4)] z-50 p-1.5 flex flex-col gap-1 animate-fade-in text-[var(--text-main)]"
          role="listbox"
        >
          {/* Menu Header */}
          <div className="px-2.5 py-1.5 text-[9px] font-mono font-bold text-[var(--accent)] uppercase tracking-widest border-b app-border flex items-center justify-between">
            <span>Inference Model Engine</span>
            <span className="text-[8px] px-1.5 py-0.5 rounded bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)]">
              {isLoading ? 'DISCOVERING...' : `${models.length} Available`}
            </span>
          </div>

          {/* Model Options List or Skeleton Loader */}
          {isLoading ? (
            <SkinLoader type="model" />
          ) : (
            <div className="flex flex-col gap-1 max-h-[240px] overflow-y-auto scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent pr-0.5">
              {models.map((option) => {
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
                        ? 'bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] font-semibold'
                        : 'border border-transparent hover:bg-[var(--accent-subtle)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
                    }`}
                    role="option"
                    aria-selected={isSelected}
                  >
                    <div className={`mt-0.5 p-1.5 rounded-lg border shrink-0 transition-colors ${
                      isSelected 
                        ? 'bg-[var(--accent-subtle)] border-[var(--accent-border)]' 
                        : 'bg-[var(--bg-base)] app-border group-hover:border-[var(--accent-border)]'
                    }`}>
                      {option.icon}
                    </div>
                    
                    <div className="flex flex-col flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span className={`text-[11px] font-mono font-bold truncate ${
                          isSelected ? 'text-[var(--accent)]' : 'text-[var(--text-main)]'
                        }`}>
                          {option.name}
                        </span>
                        {isSelected ? (
                          <IconCheck className="text-[var(--accent)] text-xs shrink-0" />
                        ) : (
                          <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-[var(--bg-base)] text-[var(--text-muted)] border app-border">
                            {option.tag}
                          </span>
                        )}
                      </div>
                      <span className="text-[9.5px] text-[var(--text-muted)] leading-relaxed font-sans line-clamp-2 mt-0.5">
                        {option.description}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};