import React, { useState } from 'react';
import { useThemeStore } from '../../store/themeStore';
import { IconSun, IconMoon, IconBack, IconSnow, IconStars } from './Icons';

export const ThemeToggle: React.FC = () => {
  const { themeMode, toggleDarkLight, setLightVariant } = useThemeStore();
  const [isSlideOpen, setIsSlideOpen] = useState(false);

  const isDark = themeMode === 'd';

  return (
    <div className="relative flex items-center select-none font-mono">
      {/* Expanded 3 Light Themes Drawer (Icon-Only Symbols) */}
      <div 
        className={`flex items-center gap-1 overflow-hidden transition-all duration-300 ease-in-out ${
          isSlideOpen ? 'max-w-32 opacity-100 pr-1' : 'max-w-0 opacity-0 pointer-events-none'
        }`}
      >
        {/* L1 Variant Option: Sun Symbol */}
        <button
          onClick={() => {
            setLightVariant('l1');
            setIsSlideOpen(false);
          }}
          className={`w-6 h-6 rounded-lg flex items-center justify-center border transition-all cursor-pointer ${
            themeMode === 'l1'
              ? 'bg-amber-400/20 text-amber-500 border-amber-400/50 shadow-xs'
              : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-transparent hover:text-amber-500 hover:bg-white/5'
          }`}
          title="L1: Claude Warm Light (Sun)"
        >
          <IconSun className="text-[10px] text-amber-500 stroke-[2.5]" />
        </button>

        {/* L2 Variant Option: Snowflake Symbol */}
        <button
          onClick={() => {
            setLightVariant('l2');
            setIsSlideOpen(false);
          }}
          className={`w-6 h-6 rounded-lg flex items-center justify-center border transition-all cursor-pointer ${
            themeMode === 'l2'
              ? 'bg-sky-400/20 text-sky-500 border-sky-400/50 shadow-xs'
              : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-transparent hover:text-sky-500 hover:bg-white/5'
          }`}
          title="L2: Arctic Slate Light (Snowflake)"
        >
          <IconSnow className="text-[10px] text-sky-400" />
        </button>

        {/* L3 Variant Option: Sparkle Symbol */}
        <button
          onClick={() => {
            setLightVariant('l3');
            setIsSlideOpen(false);
          }}
          className={`w-6 h-6 rounded-lg flex items-center justify-center border transition-all cursor-pointer ${
            themeMode === 'l3'
              ? 'bg-violet-400/20 text-violet-500 border-violet-400/50 shadow-xs'
              : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-transparent hover:text-violet-500 hover:bg-white/5'
          }`}
          title="L3: Iris Pearl Light (Sparkles)"
        >
          <IconStars className="text-[10px] text-violet-400" />
        </button>
      </div>

      {/* Main Rounded Pill Container: [ < | ☀️ / 🌙 ] */}
      <div className="flex items-center rounded-xl border app-border bg-[var(--bg-card)] shadow-2xs overflow-hidden p-0.5">
        {/* Left "<" Slide Trigger Button */}
        <button
          onClick={() => setIsSlideOpen(!isSlideOpen)}
          className="w-6 h-6 flex items-center justify-center rounded-lg text-xs font-black text-[var(--text-main)] hover:bg-[var(--accent-subtle)] hover:text-[var(--accent)] transition-all cursor-pointer"
          title="Slide out light theme symbols"
        >
          <IconBack className={`text-xs transition-transform duration-300 stroke-[2.5] ${isSlideOpen ? 'rotate-180 text-[var(--accent)]' : ''}`} />
        </button>

        {/* Right Dynamic Theme Toggle Button */}
        <button
          onClick={toggleDarkLight}
          className="w-6.5 h-6 flex items-center justify-center rounded-lg bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] transition-all cursor-pointer hover:scale-105 active:scale-95 ml-0.5 shadow-2xs"
          title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {isDark ? (
            <IconMoon className="text-[11px] stroke-[2.5]" />
          ) : themeMode === 'l2' ? (
            <IconSnow className="text-[11px] text-sky-400" />
          ) : themeMode === 'l3' ? (
            <IconStars className="text-[11px] text-violet-400" />
          ) : (
            <IconSun className="text-[11px] text-amber-500 fill-amber-400/30 stroke-[2.5]" />
          )}
        </button>
      </div>
    </div>
  );
};