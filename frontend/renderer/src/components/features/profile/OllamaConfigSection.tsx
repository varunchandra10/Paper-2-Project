import React, { useState, useEffect } from 'react';
import { IconLink, IconInfo, IconLoader } from '../../ui/Icons';

interface OllamaConfigSectionProps {
  value: string;
  onChange: (url: string) => void;
}

export const OllamaConfigSection: React.FC<OllamaConfigSectionProps> = ({
  value,
  onChange,
}) => {
  const [ollamaStatus, setOllamaStatus] = useState<'unchecked' | 'online' | 'offline'>('unchecked');
  const [isTestingOllama, setIsTestingOllama] = useState(false);
  const [showOllamaHelp, setShowOllamaHelp] = useState(false);

  // Dynamic Ollama connection checker
  const checkOllamaConnection = async (url: string) => {
    if (!url.trim()) {
      setOllamaStatus('unchecked');
      return;
    }
    setIsTestingOllama(true);
    try {
      let endpoint = url.trim();
      if (!/^https?:\/\//i.test(endpoint)) {
        endpoint = `http://${endpoint}`;
      }
      
      const res = await fetch(endpoint, { 
        method: 'GET',
        mode: 'cors',
        headers: { 'Accept': 'application/json' }
      }).catch(() => null);

      if (res && (res.status === 200 || res.ok)) {
        setOllamaStatus('online');
      } else {
        setOllamaStatus('offline');
      }
    } catch {
      setOllamaStatus('offline');
    } finally {
      setIsTestingOllama(false);
    }
  };

  useEffect(() => {
    if (value) {
      checkOllamaConnection(value);
    }
  }, []);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between items-center">
        <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1 flex items-center gap-1.5 select-none">
          <span>Ollama Local Link</span>
          <button
            type="button"
            onClick={() => setShowOllamaHelp(prev => !prev)}
            className="text-[var(--accent)] hover:bg-[var(--accent-subtle)] p-0.5 rounded transition-all cursor-pointer"
            title="Show Ollama Connection Guide"
          >
            <IconInfo className="text-xs shrink-0" />
          </button>
        </label>
        {value.trim() && (
          <button 
            type="button"
            onClick={() => checkOllamaConnection(value)}
            disabled={isTestingOllama}
            className="text-[9px] font-mono px-2.5 py-0.5 rounded-lg border bg-[var(--bg-base)] text-[var(--text-muted)] app-border hover:text-[var(--text-main)] transition-all cursor-pointer select-none flex items-center gap-1"
          >
            {isTestingOllama ? (
              <>
                <IconLoader className="text-xs animate-spin text-[var(--accent)]" />
                <span>TESTING...</span>
              </>
            ) : (
              'TEST CONNECTION'
            )}
          </button>
        )}
      </div>
      <div className="relative">
        <IconLink className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
        <input 
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOllamaStatus('unchecked');
          }}
          placeholder="e.g. http://localhost:11434"
          className="w-full pl-9 pr-24 py-2.5 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
        />
        
        {/* Status Badge */}
        <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center select-none pointer-events-none">
          {ollamaStatus === 'online' && (
            <span className="text-[8.5px] font-mono font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-md flex items-center gap-1.5 shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 animate-pulse" />
              ONLINE
            </span>
          )}
          {ollamaStatus === 'offline' && (
            <span className="text-[8.5px] font-mono font-bold text-red-400 bg-red-500/15 border border-red-500/30 px-2 py-0.5 rounded-md flex items-center gap-1.5 shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
              OFFLINE
            </span>
          )}
          {ollamaStatus === 'unchecked' && value.trim() && (
            <span className="text-[8.5px] font-mono font-bold text-[var(--text-muted)] bg-[var(--bg-base)] border app-border px-2 py-0.5 rounded-md">
              UNCHECKED
            </span>
          )}
        </div>
      </div>

      {/* Connection Guide Accordion */}
      {showOllamaHelp && (
        <div className="mt-2 p-4 rounded-xl border border-[var(--accent-border)] bg-[var(--accent-subtle)] text-xs leading-relaxed text-[var(--text-main)] font-sans animate-fade-in flex flex-col gap-2">
          <div className="font-bold text-[var(--accent)] flex items-center gap-1.5 font-mono text-[11px]">
            <span>🦙 Ollama Connection & Installation Guide</span>
          </div>
          <p className="text-[11px] text-[var(--text-muted)]">
            Use offline LLMs locally instead of paid cloud APIs by running an Ollama service instance:
          </p>
          <ol className="list-decimal list-inside pl-0.5 space-y-1.5 text-[11px] text-[var(--text-muted)]">
            <li>
              <span className="font-semibold text-[var(--text-main)]">Install Ollama:</span> Setup installer from{' '}
              <a 
                href="https://ollama.com" 
                target="_blank" 
                rel="noreferrer" 
                className="text-[var(--accent)] hover:underline inline-flex items-center gap-0.5 font-bold"
              >
                ollama.com
              </a>.
            </li>
            <li>
              <span className="font-semibold text-[var(--text-main)]">Download Model:</span> Open terminal and execute:
              <code className="block mt-1.5 p-2.5 rounded-xl bg-[var(--bg-base)] border app-border text-[10.5px] text-[var(--text-main)] select-all font-mono">
                ollama run llama3
              </code>
            </li>
            <li>
              <span className="font-semibold text-[var(--text-main)]">Paste Endpoint URL:</span> Default Ollama address is <code className="px-1.5 py-0.5 rounded-lg bg-[var(--bg-base)] border app-border text-[10.5px] text-[var(--accent)] font-bold select-all font-mono">http://localhost:11434</code>.
            </li>
          </ol>
        </div>
      )}
    </div>
  );
};
