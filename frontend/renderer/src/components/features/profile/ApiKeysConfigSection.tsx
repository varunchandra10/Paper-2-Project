import React, { useState } from 'react';
import { IconEye, IconEyeOff } from '../../ui/Icons';

interface ApiKeysConfigSectionProps {
  groqKey: string;
  setGroqKey: (key: string) => void;
  openrouterKey: string;
  setOpenrouterKey: (key: string) => void;
}

export const ApiKeysConfigSection: React.FC<ApiKeysConfigSectionProps> = ({
  groqKey,
  setGroqKey,
  openrouterKey,
  setOpenrouterKey
}) => {
  const [showGroq, setShowGroq] = useState(false);
  const [showOpenRouter, setShowOpenRouter] = useState(false);

  return (
    <div className="bg-[var(--bg-card)] border app-border rounded-2xl p-5 shadow-lg flex flex-col justify-between h-full relative overflow-hidden backdrop-blur-md gap-3">
      <div className="absolute -top-12 -right-12 w-28 h-28 bg-[var(--accent-subtle)] rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="border-b app-border pb-2.5 flex items-center justify-between select-none">
        <h3 className="text-xs font-mono font-bold text-[var(--accent)] uppercase tracking-wider flex items-center gap-2">
          <span>🔑 API Keys (Bring Your Own Key)</span>
        </h3>
        <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]">
          PRIVATE LIMITS
        </span>
      </div>

      <p className="text-[11px] text-[var(--text-muted)] leading-relaxed font-sans">
        Paste your free API keys below for <strong>private, dedicated quotas</strong>. If left empty, queries safely fall back to system default keys.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
        {/* Groq Key Input */}
        <div className="flex flex-col gap-1.5">
          <div className="flex flex-col gap-0.5">
            <label className="text-[11px] font-mono font-bold text-[var(--text-main)] uppercase tracking-wider pl-0.5">
              Groq API Key
            </label>
            <div className="flex justify-between items-center text-[10px] font-mono pl-0.5">
              <span className="text-[var(--accent)] font-semibold">(14,400/day free)</span>
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noreferrer"
                className="text-[var(--text-muted)] hover:text-[var(--accent)] flex items-center gap-1 transition-colors group"
              >
                <span className="group-hover:underline">Get free key</span>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-70 group-hover:opacity-100">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
              </a>
            </div>
          </div>

          <div className="relative">
            <input
              type={showGroq ? 'text' : 'password'}
              value={groqKey}
              onChange={(e) => setGroqKey(e.target.value)}
              placeholder="gsk_..."
              className="w-full pl-3 pr-10 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowGroq(!showGroq)}
              title={showGroq ? 'Hide API key' : 'Show API key'}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-sm text-[var(--text-muted)] hover:text-[var(--accent)] cursor-pointer select-none transition-colors p-1"
            >
              {showGroq ? <IconEyeOff /> : <IconEye />}
            </button>
          </div>
        </div>

        {/* OpenRouter Key Input */}
        <div className="flex flex-col gap-1.5">
          <div className="flex flex-col gap-0.5">
            <label className="text-[11px] font-mono font-bold text-[var(--text-main)] uppercase tracking-wider pl-0.5">
              OpenRouter API Key
            </label>
            <div className="flex justify-between items-center text-[10px] font-mono pl-0.5">
              <span className="text-[var(--accent)] font-semibold">(200/day free)</span>
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noreferrer"
                className="text-[var(--text-muted)] hover:text-[var(--accent)] flex items-center gap-1 transition-colors group"
              >
                <span className="group-hover:underline">Get free key</span>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-70 group-hover:opacity-100">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
              </a>
            </div>
          </div>

          <div className="relative">
            <input
              type={showOpenRouter ? 'text' : 'password'}
              value={openrouterKey}
              onChange={(e) => setOpenrouterKey(e.target.value)}
              placeholder="sk-or-..."
              className="w-full pl-3 pr-10 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowOpenRouter(!showOpenRouter)}
              title={showOpenRouter ? 'Hide API key' : 'Show API key'}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-sm text-[var(--text-muted)] hover:text-[var(--accent)] cursor-pointer select-none transition-colors p-1"
            >
              {showOpenRouter ? <IconEyeOff /> : <IconEye />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
