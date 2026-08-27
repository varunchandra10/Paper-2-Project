import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { ThemeToggle } from '../ui/ThemeToggle';
import { FiMaximize2, FiMinimize2, FiFileText, FiTerminal } from 'react-icons/fi';
import { FaTimes } from 'react-icons/fa';

interface HeaderProps {
  isMaximized: boolean;
  handleToggleMaximize: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isMaximized,
  handleToggleMaximize,
  isSidebarOpen,
  onToggleSidebar,
}) => {
  const {
    togglePanel,
    isHistoryOpen,
    toggleHistory,
    isLogsOpen,
    toggleLogs,
  } = usePanelStore();

  return (
    <header className="h-[52px] border-b border-border/40 px-3 flex items-center justify-between bg-card/80 backdrop-blur-xl z-20 shrink-0 select-none shadow-xs">

      {/* ── Left Section: Sidebar Toggle or Monogram Logo ── */}
      <div className="flex items-center gap-3">
        {/* Hamburger Toggle (Maximized View) */}
        {isMaximized && (
          <button
            onClick={onToggleSidebar}
            className={`p-2 rounded-xl transition-all duration-200 cursor-pointer flex flex-col gap-[4px] items-center justify-center w-8 h-8 shrink-0 group border ${
              isSidebarOpen
                ? 'text-brass bg-brass/10 border-brass/30 hover:bg-brass/15'
                : 'text-muted-foreground border-border/40 hover:bg-muted/60 hover:text-foreground'
            }`}
            title={isSidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
            aria-label="Toggle sidebar"
          >
            {/* Animated hamburger lines */}
            <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-3.5' : 'w-4'}`} />
            <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-2.5' : 'w-4'}`} />
            <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-3.5' : 'w-4'}`} />
          </button>
        )}

        {/* Branding Monogram (Compact View) */}
        {!isMaximized && (
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-brass/20 to-brass/5 flex items-center justify-center font-serif text-[10px] font-bold text-brass border border-brass/30 shrink-0 shadow-[0_0_8px_rgba(212,175,55,0.12)]">
              S
            </div>
            <h1 className="text-xs font-black tracking-[0.25em] font-mono bg-gradient-to-r from-brass via-brass/90 to-foreground text-transparent bg-clip-text">
              SYNTHEXIS
            </h1>
          </div>
        )}
      </div>

      {/* ── Right Section: Unified Pill Toolbar ── */}
      <div className="flex items-center gap-1.5 p-1 border border-border/50 rounded-full bg-muted/40 backdrop-blur-md shadow-inner select-none">

        {/* 1. Theme Switcher */}
        <div className="flex items-center px-0.5">
          <ThemeToggle />
        </div>

        {isMaximized && (
          <>
            <div className="w-[1px] h-3.5 bg-border/40 my-auto" />

            {/* 2. Documents Toggle */}
            <button
              onClick={toggleHistory}
              className={`w-6 h-6 rounded-full text-xs transition-all duration-200 cursor-pointer flex items-center justify-center ${
                isHistoryOpen
                  ? 'bg-red-500/20 text-red-400 shadow-[0_0_8px_rgba(239,68,68,0.2)]'
                  : 'text-muted-foreground hover:bg-red-500/10 hover:text-red-400'
              }`}
              title="Documents & History"
            >
              <FiFileText className="text-[11px]" />
            </button>

            {/* 3. Terminal Toggle */}
            <button
              onClick={toggleLogs}
              className={`w-6 h-6 rounded-full text-xs transition-all duration-200 cursor-pointer flex items-center justify-center ${
                isLogsOpen
                  ? 'bg-amber-500/20 text-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.2)]'
                  : 'text-muted-foreground hover:bg-amber-500/10 hover:text-amber-400'
              }`}
              title="Terminal Console"
            >
              <FiTerminal className="text-[11px]" />
            </button>
          </>
        )}

        <div className="w-[1px] h-3.5 bg-border/40 my-auto" />

        {/* 4. Maximize / Restore */}
        <button
          onClick={handleToggleMaximize}
          className="w-6 h-6 rounded-full text-xs text-muted-foreground hover:bg-brass/15 hover:text-brass transition-all duration-200 cursor-pointer flex items-center justify-center active:scale-95"
          title={isMaximized ? 'Restore Viewport' : 'Maximize Viewport'}
        >
          {isMaximized ? <FiMinimize2 className="text-[11px]" /> : <FiMaximize2 className="text-[11px]" />}
        </button>

        {/* 5. Close Button */}
        <button
          onClick={() => togglePanel()}
          className="w-6 h-6 rounded-full text-xs text-muted-foreground hover:bg-red-500/20 hover:text-red-400 transition-all duration-200 cursor-pointer flex items-center justify-center active:scale-95"
          title="Close Panel"
        >
          <FaTimes className="text-[10px]" />
        </button>
      </div>
    </header>
  );
};