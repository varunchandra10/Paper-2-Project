import React, { useState } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { useThemeStore } from '../../store/themeStore';
import { FiMaximize, FiMinimize, FiX, FiSun, FiMoon, FiChevronLeft } from 'react-icons/fi';
import { BsSnow, BsStars } from 'react-icons/bs';

interface HeaderProps {
  isMaximized: boolean;
  handleToggleMaximize: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isMaximized,
  handleToggleMaximize,
}) => {
  const { togglePanel, activePaper } = usePanelStore();
  const { themeMode, toggleDarkLight, setLightVariant } = useThemeStore();
  const [isSlideOpen, setIsSlideOpen] = useState(false);

  const isDark = themeMode === 'd';

  const handleMinimize = () => {
    if (window.electronAPI?.minimizeWindow) {
      window.electronAPI.minimizeWindow();
    } else {
      togglePanel();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI?.maximizeWindow) {
      window.electronAPI.maximizeWindow();
    } else {
      handleToggleMaximize();
    }
  };

  const handleClose = () => {
    if (window.electronAPI?.closeWindow) {
      window.electronAPI.closeWindow();
    } else {
      togglePanel();
    }
  };

  return (
    <header className="h-12 app-rail flex items-center justify-between px-4 shrink-0 z-40 transition-colors border-none select-none">
      {/* ── Left: Logo + Paper Title ── */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Logo Mark */}
        <div 
          className="w-7 h-7 rounded-lg accent-pill flex items-center justify-center font-heading font-extrabold text-xs cursor-pointer hover:scale-105 transition-transform shrink-0" 
          title="Synthexis AI"
        >
          SX
        </div>
        {/* Separator */}
        <span className="w-px h-4 bg-[var(--border-color)] opacity-50 shrink-0" />
        {/* Active Paper */}
        <span className="w-2 h-2 rounded-full bg-[var(--accent)] shrink-0" />
        <span className="font-heading font-semibold text-xs text-[var(--text-main)] truncate max-w-xs sm:max-w-md">
          {activePaper?.title || 'Synthexis'}
        </span>
      </div>

      {/* ── Right: Theme Switcher + Window Controls ── */}
      <div className="flex items-center gap-2.5 shrink-0">

        {/* Slide-out Theme Switcher Pill [ < | ☀️ / 🌙 ] */}
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
              <FiSun className="text-[10px] text-amber-500 stroke-[2.5]" />
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
              <BsSnow className="text-[10px] text-sky-400" />
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
              <BsStars className="text-[10px] text-violet-400" />
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
              <FiChevronLeft className={`text-xs transition-transform duration-300 stroke-[2.5] ${isSlideOpen ? 'rotate-180 text-[var(--accent)]' : ''}`} />
            </button>

            {/* Right Dynamic Theme Toggle Button */}
            <button
              onClick={toggleDarkLight}
              className="w-6.5 h-6 flex items-center justify-center rounded-lg bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] transition-all cursor-pointer hover:scale-105 active:scale-95 ml-0.5 shadow-2xs"
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {isDark ? (
                <FiMoon className="text-[11px] stroke-[2.5]" />
              ) : themeMode === 'l2' ? (
                <BsSnow className="text-[11px] text-sky-400" />
              ) : themeMode === 'l3' ? (
                <BsStars className="text-[11px] text-violet-400" />
              ) : (
                <FiSun className="text-[11px] text-amber-500 fill-amber-400/30 stroke-[2.5]" />
              )}
            </button>
          </div>
        </div>

        {/* Window Controls: Toggle Maximize/Minimize (Single Button) & Close */}
        <div className="flex items-center gap-1 pl-2 border-l app-border">
          {/* Single Maximize/Minimize Toggle Button */}
          <button 
            onClick={handleMaximize} 
            title={isMaximized ? "Minimize Screen" : "Maximize Screen"} 
            className="w-6.5 h-6.5 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-white/10 hover:text-[var(--text-main)] transition-all cursor-pointer active:scale-95"
          >
            {isMaximized ? (
              <FiMinimize className="text-[11px] text-[var(--accent)]" />
            ) : (
              <FiMaximize className="text-[11px]" />
            )}
          </button>

          {/* Close Button */}
          <button 
            onClick={handleClose} 
            title="Close Window" 
            className="w-6.5 h-6.5 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-red-500/80 hover:text-white transition-all cursor-pointer active:scale-95"
          >
            <FiX className="text-xs" />
          </button>
        </div>
      </div>
    </header>
  );
};