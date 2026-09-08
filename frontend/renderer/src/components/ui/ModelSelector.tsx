import React, { useState, useRef, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { API_BASE } from '../../store/utils/storeUtils';
import { SkinLoader } from './SkinLoader';
import { IconUp, IconCheck } from './Icons';

import {
  type ModelOption,
  FALLBACK_GROQ,
  FALLBACK_OPENROUTER,
  isExcludedModel as isExcluded
} from '../../constants/models';

export type { ModelOption };

export const ModelSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [localModels, setLocalModels] = useState<ModelOption[]>([]);
  const [groqModels, setGroqModels] = useState<ModelOption[]>(FALLBACK_GROQ);
  const [openrouterModels, setOpenrouterModels] = useState<ModelOption[]>(FALLBACK_OPENROUTER);
  const [allModels, setAllModels] = useState<ModelOption[]>([...FALLBACK_GROQ, ...FALLBACK_OPENROUTER]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [groqLimits, setGroqLimits] = useState<number | null>(null);
  const [orLimits, setOrLimits] = useState<number | null>(null);

  const { selectedModel, setSelectedModel, setActiveView } = usePanelStore();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeOption = allModels.find(opt => opt.id === selectedModel) || {
    id: selectedModel,
    name: selectedModel ? (selectedModel.includes('/') ? selectedModel.split('/')[1] : selectedModel) : 'Select Model',
    provider: 'Cloud'
  };

  const fetchQuotaMetrics = async () => {
    try {
      const res = await fetch(`${API_BASE}/models/limits`);
      if (res.ok) {
        const data = await res.json();
        const gPct = data.limits?.groq?.weekly?.remaining_pct;
        const oPct = data.limits?.openrouter?.weekly?.remaining_pct;
        if (typeof gPct === 'number') setGroqLimits(gPct);
        if (typeof oPct === 'number') setOrLimits(oPct);
      }
    } catch {
      // silent
    }
  };

  useEffect(() => {
    let isMounted = true;
    const fetchModels = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`${API_BASE}/models`);
        if (res.ok) {
          const data = await res.json();
          const groups = data.groups || {};

          const mapModel = (m: any, defaultProvider: string, isLocal = false): ModelOption => ({
            id: m.id,
            name: m.name || m.id,
            provider: m.provider || defaultProvider,
            is_local: isLocal || m.is_local === true,
            description: m.description
          });

          // 1. Local Models from Ollama
          const localList: ModelOption[] = (groups.local?.models || [])
            .filter((m: any) => !isExcluded(m))
            .map((m: any) => mapModel(m, 'Local Ollama', true));

          // 2. Groq Models
          const groqList: ModelOption[] = (groups.groq?.models || FALLBACK_GROQ)
            .filter((m: any) => !isExcluded(m))
            .map((m: any) => mapModel(m, 'Groq'));

          // 3. OpenRouter Models
          const orList: ModelOption[] = (groups.openrouter?.models || FALLBACK_OPENROUTER)
            .filter((m: any) => !isExcluded(m))
            .map((m: any) => mapModel(m, 'OpenRouter'));

          if (isMounted) {
            setLocalModels(localList);
            setGroqModels(groqList);
            setOpenrouterModels(orList);

            const combined = [...groqList, ...orList, ...localList];
            setAllModels(combined);

            if (!selectedModel || !combined.some(m => m.id === selectedModel)) {
              if (groqList.length > 0) {
                setSelectedModel(groqList[0].id);
              } else if (orList.length > 0) {
                setSelectedModel(orList[0].id);
              } else if (localList.length > 0) {
                setSelectedModel(localList[0].id);
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch dynamic inference models:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchModels();
    fetchQuotaMetrics();

    // Listen to live rate limit updates when PDFs are sent
    const handleLimitsRefresh = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent?.detail?.limits) {
        const l = customEvent.detail.limits;
        if (typeof l?.groq?.weekly?.remaining_pct === 'number') setGroqLimits(l.groq.weekly.remaining_pct);
        if (typeof l?.openrouter?.weekly?.remaining_pct === 'number') setOrLimits(l.openrouter.weekly.remaining_pct);
      }
      fetchQuotaMetrics();
    };
    window.addEventListener('refresh-model-limits', handleLimitsRefresh);
    // Poll model quota metrics every 5 minutes (300,000ms) rather than spamming every 6s
    const interval = setInterval(fetchQuotaMetrics, 300000);

    return () => { 
      isMounted = false; 
      window.removeEventListener('refresh-model-limits', handleLimitsRefresh);
      clearInterval(interval);
    };
  }, []);

  // Refresh metrics when user opens the dropdown
  useEffect(() => {
    if (isOpen) {
      fetchQuotaMetrics();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const renderModelItem = (option: ModelOption) => {
    const isSelected = selectedModel === option.id;
    return (
      <div
        key={option.id}
        onClick={() => {
          setSelectedModel(option.id);
          setIsOpen(false);
        }}
        className={`flex items-center justify-between px-3 py-1.5 rounded-lg text-[11px] font-mono transition-colors cursor-pointer ${
          isSelected
            ? 'bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold'
            : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
        }`}
        role="option"
        aria-selected={isSelected}
      >
        <div className="flex items-center gap-1.5 truncate">
          <span className="truncate">{option.name}</span>
        </div>
        {isSelected && <IconCheck className="text-[var(--accent)] text-xs shrink-0 ml-2" />}
      </div>
    );
  };

  return (
    <div className="relative font-mono select-none" ref={dropdownRef}>
      {/* Dropdown Toggle Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg border transition-all duration-200 text-[11px] font-mono outline-none cursor-pointer active:scale-[0.98] ${
          isOpen 
            ? 'border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--text-main)] shadow-xs' 
            : 'border-[var(--border-color)] bg-[var(--bg-base)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
        }`}
        title="Select Active Inference Model"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="font-semibold text-[11px] text-[var(--text-main)] truncate max-w-[150px] leading-none">
          {activeOption.name}
        </span>
        <IconUp 
          className={`text-xs text-[var(--text-muted)] transition-transform duration-200 shrink-0 ${
            isOpen ? 'rotate-180 text-[var(--accent)]' : ''
          }`} 
        />
      </button>

      {/* Floating Dropdown Option List */}
      {isOpen && (
        <div 
          className="absolute bottom-[calc(100%+8px)] left-0 w-[260px] max-w-[calc(100vw-32px)] bg-[var(--bg-card)] border app-border rounded-xl shadow-[0_12px_32px_rgba(0,0,0,0.4)] z-50 p-2 flex flex-col gap-1.5 animate-fade-in text-[var(--text-main)]"
          role="listbox"
        >
          {/* Menu Header */}
          <div className="px-2 py-1 text-[9px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider border-b app-border">
            Select Inference Model
          </div>

          {/* Model Options Grouped List or Skeleton Loader */}
          {isLoading ? (
            <SkinLoader type="model" />
          ) : (
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent pr-0.5">
              {/* ─── Group 1: Groq Models ─── */}
              <div className="flex flex-col gap-0.5">
                <div className="px-2 pt-1 pb-0.5 flex items-center justify-between text-[8.5px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  <span>Groq Models</span>
                  {/* [LEGACY BADGE - PRESERVED & COMMENTED OUT] */}
                  {/*
                  <span className="px-1.5 py-0.5 rounded text-[7.5px] bg-amber-500/15 text-amber-400 font-bold border border-amber-500/30">
                    FREE TIER
                  </span>
                  */}
                  <span className="px-1.5 py-0.5 rounded text-[7.5px] bg-amber-500/15 text-amber-400 font-bold border border-amber-500/30">
                    {groqLimits !== null ? `${groqLimits}% REMAINING` : 'FREE TIER'}
                  </span>
                </div>
                {groqModels.map(renderModelItem)}
              </div>

              {/* ─── Group 2: OpenRouter Models ─── */}
              <div className="flex flex-col gap-0.5 pt-1 border-t app-border">
                <div className="px-2 pt-1 pb-0.5 flex items-center justify-between text-[8.5px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  <span>OpenRouter Models</span>
                  {/* [LEGACY BADGE - PRESERVED & COMMENTED OUT] */}
                  {/*
                  <span className="px-1.5 py-0.5 rounded text-[7.5px] bg-sky-500/15 text-sky-400 font-bold border border-sky-500/30">
                    FREE TIER
                  </span>
                  */}
                  <span className="px-1.5 py-0.5 rounded text-[7.5px] bg-sky-500/15 text-sky-400 font-bold border border-sky-500/30">
                    {orLimits !== null ? `${orLimits}% REMAINING` : 'FREE TIER'}
                  </span>
                </div>
                {openrouterModels.map(renderModelItem)}
              </div>

              {/* ─── Group 3: Local Models (Ollama) ─── */}
              <div className="flex flex-col gap-0.5 pt-1 border-t app-border">
                <div className="px-2 pt-1 pb-0.5 flex items-center justify-between text-[8.5px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  <span>Local Models (Ollama)</span>
                  <span className={`px-1.5 py-0.5 rounded text-[7.5px] font-bold border ${
                    localModels.length > 0 
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' 
                      : 'bg-[var(--accent-subtle)] text-[var(--text-muted)] border-[var(--border-color)]'
                  }`}>
                    {localModels.length > 0 ? `${localModels.length} DETECTED` : '0 MODELS'}
                  </span>
                </div>

                {localModels.length > 0 ? (
                  localModels.map(renderModelItem)
                ) : (
                  <div className="px-2.5 py-2 rounded-lg text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-base)]/60 border border-dashed border-[var(--border-color)] flex flex-col gap-0.5 select-none my-0.5">
                    <div className="flex items-center justify-between text-[var(--text-muted)] font-semibold">
                      <span>0 local models found</span>
                      <span className="text-[8px] px-1.5 py-0.2 rounded bg-[var(--accent-subtle)] text-[var(--text-muted)] border border-[var(--border-color)] font-bold">0 MODELS</span>
                    </div>
                    <span className="text-[8.5px] text-[var(--text-muted)] leading-tight">
                      Run <span className="text-[var(--accent)] font-semibold">ollama pull &lt;model&gt;</span> or check Ollama in Profile.
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quick Limits & Quotas Action Footer */}
          <div className="pt-1.5 mt-1 border-t app-border">
            <button
              type="button"
              onClick={() => {
                setActiveView('profile');
                setIsOpen(false);
              }}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-[10px] font-mono font-bold text-[var(--accent)] hover:bg-[var(--accent-subtle)] transition-colors cursor-pointer border border-[var(--accent-border)]/40 hover:border-[var(--accent)]"
            >
              <span>⚡ View Rate Limits & Quotas</span>
              <span className="text-xs">↗</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};