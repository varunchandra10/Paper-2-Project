import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { ThemeToggle } from '../ui/ThemeToggle';
import { IconMaximize, IconMinimize, IconClose } from '../ui/Icons';

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
  const { togglePanel, uploadedFileName, activePaperId } = usePanelStore();

  const handleMaximize = () => {
    if (window.mascotAPI?.toggleMaximize) {
      window.mascotAPI.toggleMaximize();
    } else {
      handleToggleMaximize();
    }
  };

  const handleClose = () => {
    if (window.mascotAPI?.togglePanel) {
      window.mascotAPI.togglePanel();
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
          {uploadedFileName || activePaperId || 'Synthexis'}
        </span>
      </div>

      {/* ── Right: Theme Switcher + Window Controls ── */}
      <div className="flex items-center gap-2.5 shrink-0">

        {/* Encapsulated Theme Toggle Component */}
        <ThemeToggle />

        {/* Window Controls: Toggle Maximize/Minimize (Single Button) & Close */}
        <div className="flex items-center gap-1 pl-2 border-l app-border">
          {/* Single Maximize/Minimize Toggle Button */}
          <button 
            onClick={handleMaximize} 
            title={isMaximized ? "Minimize Screen" : "Maximize Screen"} 
            className="w-6.5 h-6.5 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-[var(--accent-subtle)] hover:text-[var(--accent)] transition-all cursor-pointer active:scale-95"
          >
            {isMaximized ? (
              <IconMinimize className="text-[11px] text-[var(--accent)]" />
            ) : (
              <IconMaximize className="text-[11px]" />
            )}
          </button>

          {/* Close Button */}
          <button 
            onClick={handleClose} 
            title="Close Window" 
            className="w-6.5 h-6.5 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-red-500/80 hover:text-white transition-all cursor-pointer active:scale-95"
          >
            <IconClose className="text-xs" />
          </button>
        </div>
      </div>
    </header>
  );
};