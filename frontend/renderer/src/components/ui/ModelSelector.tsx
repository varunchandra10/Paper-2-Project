import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaChevronUp, FaRobot, FaCode, FaBrain } from 'react-icons/fa6';

interface ModelOption {
  id: string;
  name: string;
  provider: string;
  description: string;
  icon: React.ReactNode;
}

const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'qwen2.5-coder:1.5b',
    name: 'Qwen 2.5 Coder (1.5B)',
    provider: 'Local / OpenRouter',
    description: 'Specialized for writing PyTorch code adapts',
    icon: <FaCode className="text-brass text-sm shrink-0" />
  },
  {
    id: 'llama-3.3-70b-versatile',
    name: 'Llama 3.3 (70B)',
    provider: 'Groq Cloud API',
    description: 'Deep logical reasoning & complex constraint checks',
    icon: <FaBrain className="text-brass text-sm shrink-0" />
  },
  {
    id: 'meta-llama/llama-3.2-3b-instruct:free',
    name: 'Llama 3.2 (3B)',
    provider: 'OpenRouter (Free)',
    description: 'Ultra-fast ingestion & lightweight parsing',
    icon: <FaRobot className="text-brass text-sm shrink-0" />
  }
];

export const ModelSelector: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  const { selectedModel, setSelectedModel } = usePanelStore();
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  const activeOption = MODEL_OPTIONS.find(opt => opt.id === selectedModel) || MODEL_OPTIONS[0];

  React.useEffect(() => {
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
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border/40 bg-card hover:bg-muted/30 text-[10px] text-foreground/80 outline-none hover:border-brass/30 transition-all duration-300 shadow-sm cursor-pointer select-none"
        title="Select Active LLM Engine"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-1.5">
          {activeOption.icon}
          <span className="font-semibold text-foreground/90">{activeOption.name}</span>
        </span>
        <FaChevronUp className={`text-[8px] text-foreground/40 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Floating Dropdown Option List */}
      {isOpen && (
        <div 
          className="absolute bottom-[42px] left-0 w-[270px] bg-card border border-border rounded-xl shadow-2xl z-50 p-1.5 flex flex-col gap-1 transition-all duration-300 select-none animate-fade-in"
          role="listbox"
        >
          <div className="px-2.5 py-1 text-[8px] font-bold text-brass/70 uppercase tracking-widest border-b border-border/5">
            Select Pipeline Model
          </div>
          {MODEL_OPTIONS.map((option) => (
            <div
              key={option.id}
              onClick={() => {
                setSelectedModel(option.id);
                setIsOpen(false);
              }}
              className={`flex items-start gap-2.5 p-2 rounded-lg transition-all duration-200 cursor-pointer ${
                selectedModel === option.id
                  ? 'bg-brass/10 border border-brass/15 text-foreground'
                  : 'border border-transparent hover:bg-muted/40 text-foreground/80'
              }`}
              role="option"
              aria-selected={selectedModel === option.id}
            >
              <div className="mt-0.5">{option.icon}</div>
              <div className="flex flex-col truncate">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold text-foreground/90 truncate">{option.name}</span>
                  <span className="text-[8px] text-foreground/40 shrink-0 font-sans">{option.provider}</span>
                </div>
                <span className="text-[8px] text-foreground/50 leading-normal truncate">{option.description}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
