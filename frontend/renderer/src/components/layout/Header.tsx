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
    <header className="h-[55px] border-b border-border/45 px-3 flex items-center gap-2 bg-background/40 backdrop-blur-xl z-20 shrink-0 select-none">

      {/* ── Hamburger (maximized only) ─────────────────────── */}
      {isMaximized && (
        <button
          onClick={onToggleSidebar}
          className={`p-2 rounded-lg transition-all duration-200 cursor-pointer flex flex-col gap-[4.5px] items-center justify-center w-9 h-9 shrink-0 ${
            isSidebarOpen
              ? 'text-brass bg-brass/10 hover:bg-brass/15'
              : 'text-foreground/50 hover:bg-foreground/8 hover:text-foreground'
          }`}
          title={isSidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
          aria-label="Toggle sidebar"
        >
          {/* Three-line hamburger drawn with spans */}
          <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-4' : 'w-4'}`} />
          <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-3' : 'w-4'}`} />
          <span className={`block h-[1.5px] rounded-full bg-current transition-all duration-300 ${isSidebarOpen ? 'w-2' : 'w-4'}`} />
        </button>
      )}

      {/* ── Logo (compact mode only — in maximized it lives in sidebar) ── */}
      {!isMaximized && (
        <div className="flex items-center border-r border-border/40 pr-4 h-full">
          <h1 className="text-xs font-black tracking-[0.2em] font-mono bg-gradient-to-r from-brass to-foreground text-transparent bg-clip-text">
            Paper_2_Project
          </h1>
        </div>
      )}

      {/* ── Spacer pushes controls to the right ─────────────── */}
      <div className="flex-1" />

      {/* ── Unified Segmented Control Group ─────────────────── */}
      <div className="flex items-center border border-border/50 rounded-xl overflow-hidden bg-black/15 divide-x divide-border/50 shadow-sm mr-1.5">

        {/* 1. Theme Toggle */}
        <ThemeToggle />

        {isMaximized && (
          <>
            {/* 2. Documents Toggle */}
            <button
              onClick={toggleHistory}
              className={`p-2.5 text-sm transition-all cursor-pointer flex items-center justify-center w-9 h-9 ${
                isHistoryOpen
                  ? 'bg-red-500/15 text-red-500'
                  : 'text-foreground/45 hover:bg-red-500/10 hover:text-red-500'
              }`}
              title="Documents & History"
            >
              <FiFileText />
            </button>

            {/* 3. Terminal Toggle */}
            <button
              onClick={toggleLogs}
              className={`p-2.5 text-sm transition-all cursor-pointer flex items-center justify-center w-9 h-9 ${
                isLogsOpen
                  ? 'bg-amber-500/15 text-amber-500'
                  : 'text-foreground/45 hover:bg-amber-500/10 hover:text-amber-500'
              }`}
              title="Terminal Console"
            >
              <FiTerminal />
            </button>
          </>
        )}

        {/* 4. Maximize / Restore */}
        <button
          onClick={handleToggleMaximize}
          className="p-2.5 text-sm text-foreground/45 hover:bg-brass/15 hover:text-brass transition-all cursor-pointer flex items-center justify-center w-9 h-9"
          title={isMaximized ? 'Restore Mascot Panel' : 'Maximize Viewport'}
        >
          {isMaximized ? <FiMinimize2 /> : <FiMaximize2 />}
        </button>

        {/* 5. Close */}
        <button
          onClick={() => window.mascotAPI ? window.mascotAPI.togglePanel() : togglePanel()}
          className="p-2.5 text-sm text-foreground/40 hover:bg-red-500/15 hover:text-red-500 transition-all cursor-pointer flex items-center justify-center w-9 h-9"
          title="Close Application"
        >
          <FaTimes />
        </button>
      </div>
    </header>
  );
};
