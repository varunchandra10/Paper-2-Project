import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { ChatHistoryList } from './ChatHistoryList';
import { DocumentHistoryList } from './DocumentHistoryList';
import { MascotBox } from './MascotBox';
import { SkinLoader } from '../ui/SkinLoader';
import { 
  IconMessageSquare, 
  IconBookOpen, 
  IconActivity,
  IconPlus,
  IconClose
} from '../ui/Icons';

interface LeftSidebarProps {
  isMaximized: boolean;
  isOpen: boolean;
  onToggleOpen?: () => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({ isMaximized, isOpen, onToggleOpen }) => {
  const { 
    resetAnalysis, 
    setActiveView,
    fetchConversations,
    conversations,
    uploadedHistory,
    hardwareMetrics,
    fetchHardwareMetrics,
    isHardwareLoading
  } = usePanelStore();
  const [activeTab, setActiveTab] = useState<'chat' | 'library' | 'feasibility'>('chat');

  // Draggable sidebar width state (persisted to localStorage)
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('ruexis_sidebar_width') || localStorage.getItem('synthexis_sidebar_width');
      return saved ? Math.max(200, Math.min(600, parseInt(saved, 10))) : 240;
    } catch {
      return 240;
    }
  });
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      // Rail width is 48px (w-12)
      const newWidth = Math.max(200, Math.min(600, e.clientX - 48));
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        try {
          localStorage.setItem('ruexis_sidebar_width', sidebarWidth.toString());
        } catch {}
      }
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, sidebarWidth]);

  const handleTabClick = (tab: 'chat' | 'library' | 'feasibility') => {
    if (isOpen) {
      // ── WHEN LEFTSIDEBAR IS OPEN ──
      if (activeTab === tab) {
        // If already showing this section -> CLOSE the leftsidebar
        if (onToggleOpen) onToggleOpen();
      } else {
        // If showing a different section -> SWITCH to clicked section history
        setActiveTab(tab);
        if (tab === 'chat') {
          setActiveView('chat');
          fetchConversations();
        } else if (tab === 'feasibility') {
          fetchHardwareMetrics();
        }
      }
    } else {
      // ── WHEN LEFTSIDEBAR IS CLOSED ──
      // OPEN the leftsidebar & show clicked section
      setActiveTab(tab);
      if (tab === 'chat') {
        setActiveView('chat');
        fetchConversations();
      } else if (tab === 'feasibility') {
        fetchHardwareMetrics();
      }
      if (onToggleOpen) onToggleOpen();
    }
  };

  const handleNewConversation = () => {
    resetAnalysis();
    setActiveTab('chat');
    setActiveView('chat');
    if (!isMaximized && isOpen && onToggleOpen) {
      onToggleOpen();
    }
  };

  return (
    <>
      {/* ── MINIMIZED MODE BACKDROP (Click outside to close) ── */}
      {!isMaximized && isOpen && (
        <div
          onClick={onToggleOpen}
          className="fixed inset-0 left-12 z-40 bg-black/35 backdrop-blur-[1.5px] transition-opacity duration-200 cursor-pointer animate-fade-in"
        />
      )}

      <div className={`flex h-full select-none ${isMaximized ? 'shrink-0 z-30' : 'relative z-50'}`}>
        {/* ── 1. VS CODE ACTIVITY BAR (Slim Icon Rail) ── */}
      <aside className="w-12 app-rail flex flex-col items-center justify-between py-2 shrink-0 transition-colors relative z-40">
        <div className="flex flex-col items-center gap-4 w-full">
          {/* Navigation Icons with Rounded Pill Hover & Active Border Styling */}
          <nav className="flex flex-col gap-2 w-full items-center">
            {/* New Conversation Plus Button */}
            <button
              onClick={handleNewConversation}
              className="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer text-[var(--accent)] bg-[var(--accent-subtle)] border border-[var(--accent-border)] hover:scale-105 active:scale-95 shadow-xs mb-1"
              data-tooltip="New Research Conversation"
              data-tooltip-pos="right"
            >
              <IconPlus className="text-xs" />
            </button>

            {/* 1st Button: Chat / Conversation History */}
            <button
              onClick={() => handleTabClick('chat')}
              className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
                activeTab === 'chat' && isOpen
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent)]/50 shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent'
              }`}
              data-tooltip="Conversational History"
              data-tooltip-pos="right"
            >
                <IconMessageSquare className="text-xs shrink-0" />
            </button>

            {/* 2nd Button: Document History */}
            <button
              onClick={() => handleTabClick('library')}
              className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
                activeTab === 'library' && isOpen
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent)]/50 shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent'
              }`}
              data-tooltip="Document History"
              data-tooltip-pos="right"
            >
                <IconBookOpen className="text-xs shrink-0" />
            </button>

            {/* 3rd Button: Hardware Radar */}
            <button
              onClick={() => handleTabClick('feasibility')}
              className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
                activeTab === 'feasibility' && isOpen
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent)]/50 shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent'
              }`}
              data-tooltip="Hardware Radar"
              data-tooltip-pos="right"
            >
                <IconActivity className="text-xs shrink-0" />
            </button>
          </nav>
        </div>

        {/* Bottom Rail Actions: Sidebar Toggle + User Profile */}
        <div className="flex flex-col items-center gap-2.5 w-full">
          {/* Sidebar Panel Toggle */}
          <button
            onClick={onToggleOpen}
            className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
              isOpen
                ? 'text-[var(--accent)] bg-[var(--accent-subtle)] border border-[var(--accent-border)]'
                : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent'
            }`}
            data-tooltip={isOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
            data-tooltip-pos="right"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="3" y="3" width="18" height="18" rx="2" strokeWidth="2" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v18" />
            </svg>
          </button>

          {/* User Profile Avatar */}
          <button
            onClick={() => setActiveView('profile')}
            className="w-7 h-7 rounded-full border app-border flex items-center justify-center font-heading font-bold text-[10px] text-[var(--text-muted)] cursor-pointer hover:border-[var(--accent)] hover:text-[var(--text-main)] hover:scale-105 transition-all"
            data-tooltip="User Profile"
            data-tooltip-pos="right"
          >
            VC
          </button>
        </div>
      </aside>

      {/* ── 2. VS CODE EXPLORER PANEL (Rounded Card Panel with Dynamic Drag Resize) ── */}
      <aside
        style={{ 
          width: isOpen 
            ? (!isMaximized ? 'min(calc(100vw - 3.75rem), 320px)' : `${sidebarWidth}px`) 
            : 0 
        }}
        className={`bg-[var(--bg-sidebar)] border app-border rounded-xl flex flex-col justify-between overflow-hidden ${
          !isMaximized
            ? 'absolute left-12 top-0 bottom-1.5 z-50 shadow-2xl backdrop-blur-md'
            : 'shrink-0 mb-1.5 shadow-xs relative'
        } ${
          isResizing ? 'transition-none select-none' : 'transition-all duration-200 ease-in-out'
        } ${
          isOpen ? `opacity-100 ${isMaximized ? 'mr-1.5' : ''}` : 'opacity-0 border-none p-0 pointer-events-none'
        }`}
      >
        <div className="w-full flex flex-col h-full overflow-hidden shrink-0">
          
          {/* Top Panel Title Header Bar */}
          <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b app-border select-none">
            <span className="text-[11px] font-sans font-bold tracking-wider text-[var(--text-muted)] uppercase">
              {activeTab === 'chat' ? 'CHAT HISTORY' : activeTab === 'library' ? 'DOCUMENT HISTORY' : 'HARDWARE RADAR'}
            </span>
            <div className="flex items-center gap-1.5">
              {activeTab === 'library' && (
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs">
                  {uploadedHistory.length}
                </span>
              )}
              {activeTab === 'chat' && (
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs">
                  {conversations.length}
                </span>
              )}
              {activeTab === 'feasibility' && (
                <span className={`text-[9.5px] px-2 py-0.5 rounded-full font-mono font-bold uppercase tracking-wider ${
                  isHardwareLoading 
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] animate-pulse' 
                    : 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs'
                }`}>
                  {isHardwareLoading ? 'PROBING...' : (hardwareMetrics?.status?.toUpperCase() || 'ONLINE')}
                </span>
              )}
              {/* Close Button for Minimized Overlay Mode */}
              {!isMaximized && (
                <button
                  onClick={onToggleOpen}
                  className="w-5 h-5 rounded-md flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] cursor-pointer transition-colors ml-1"
                  data-tooltip="Close"
                  data-tooltip-pos="bottom"
                >
                  <IconClose className="text-xs" />
                </button>
              )}
            </div>
          </div>

          {/* Render ChatHistoryList component when Chat tab is active */}
          {activeTab === 'chat' && (
            <ChatHistoryList 
              isOpen={isOpen} 
              onSelect={() => {
                if (!isMaximized && onToggleOpen) {
                  onToggleOpen();
                }
              }}
            />
          )}

          {/* Render DocumentHistoryList component when Document History (Library) tab is active */}
          {activeTab === 'library' && (
            <DocumentHistoryList 
              isOpen={isOpen} 
              onSelect={() => {
                if (!isMaximized && onToggleOpen) {
                  onToggleOpen();
                }
              }}
            />
          )}

          {/* Render Live Hardware Radar when Feasibility tab is active */}
          {activeTab === 'feasibility' && (
            <div className="p-2.5 font-mono space-y-2 overflow-y-auto flex-1 text-[10px]">
              {isHardwareLoading || !hardwareMetrics ? (
                /* ── STANDALONE SKIN LOADER COMPONENT ── */
                <SkinLoader type="hardware" />
              ) : (
                /* ── REAL LIVE DATA STATE ── */
                <>
                  {/* Host CPU & RAM Stats */}
                  <div className="p-2 rounded-lg bg-[var(--bg-base)] border app-border space-y-1">
                    <div className="text-[8.5px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5">CPU & PROCESSOR SPECS</div>
                    <div className="text-[9.5px] text-[var(--text-main)] font-bold truncate" title={hardwareMetrics?.cpu?.processor}>
                      {hardwareMetrics?.cpu?.processor || 'System Host Compute'}
                    </div>
                    <div className="flex justify-between text-[9.5px] pt-0.5">
                      <span className="text-[var(--text-muted)]">Platform:</span>
                      <span className="text-[var(--text-main)] font-bold">{hardwareMetrics?.cpu?.platform || 'Host'} ({hardwareMetrics?.cpu?.architecture || 'x64'})</span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">CPU Cores:</span>
                      <span className="text-[var(--text-main)] font-bold">{hardwareMetrics?.cpu?.cores || 8} Cores</span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">CPU Usage:</span>
                      <span className="text-[var(--accent)] font-bold">{hardwareMetrics?.cpu?.usage_percent ?? 0}%</span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">Total RAM:</span>
                      <span className="text-[var(--text-main)] font-bold">{hardwareMetrics?.cpu?.ram_total_gb ?? 16} GB</span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">Available RAM:</span>
                      <span className="text-emerald-400 font-bold">{hardwareMetrics?.cpu?.ram_available_gb ?? 8} GB</span>
                    </div>
                  </div>

                  {/* GPU / VRAM Probing Stats */}
                  <div className="p-2 rounded-lg bg-[var(--bg-base)] border app-border space-y-1">
                    <div className="text-[8.5px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5">GRAPHICS & GPU SPECS</div>
                    <div className="text-[9.5px] text-[var(--text-main)] font-bold truncate" title={hardwareMetrics?.gpu?.name}>
                      {hardwareMetrics?.gpu?.name || 'CPU / System Host Compute'}
                    </div>
                    <div className="flex justify-between text-[9.5px] pt-0.5">
                      <span className="text-[var(--text-muted)]">CUDA Acceleration:</span>
                      <span className={`font-bold ${hardwareMetrics?.gpu?.cuda_available ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
                        {hardwareMetrics?.gpu?.cuda_available ? 'Active (CUDA)' : 'Inactive (Host CPU)'}
                      </span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">Total VRAM:</span>
                      <span className="text-[var(--text-main)] font-bold">{hardwareMetrics?.gpu?.vram_total_gb ?? 0} GB</span>
                    </div>
                    <div className="flex justify-between text-[9.5px]">
                      <span className="text-[var(--text-muted)]">Free VRAM:</span>
                      <span className="text-emerald-400 font-bold">{hardwareMetrics?.gpu?.vram_free_gb ?? 0} GB</span>
                    </div>
                  </div>

                  <button
                    onClick={fetchHardwareMetrics}
                    className="w-full py-1 rounded-md border app-border bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] text-[9.5px] text-[var(--text-main)] font-bold transition-all cursor-pointer text-center"
                  >
                    ↻ Refresh Live Hardware Radar
                  </button>
                </>
              )}
            </div>
          )}

          {/* ── BOTTOM ANCHORED MASCOT COMPANION DOCK (Maximized Mode Only) ── */}
          {isMaximized && (
            <div className="p-2 border-t app-border shrink-0 bg-[var(--bg-base)]/40 flex justify-center">
              <MascotBox isOpen={isOpen} isMaximized={isMaximized} />
            </div>
          )}

        </div>

        {/* ── DRAGGABLE WIDTH RESIZER HANDLE (Ultra-Slim Minimalist Style - Maximized Only) ── */}
        {isOpen && isMaximized && (
          <div
            onMouseDown={startResizing}
            onDoubleClick={() => setSidebarWidth(240)}
            className="absolute top-0 -right-[2px] w-[6px] h-full cursor-col-resize z-40 group flex items-center justify-center select-none"
            title="Drag to resize sidebar width (double-click to reset to 240px)"
          >
            {/* Ultra-slim 1.5px vertical line indicator */}
            <div className={`w-[1.5px] h-full transition-colors duration-150 ${
              isResizing 
                ? 'bg-[var(--accent)]' 
                : 'bg-transparent group-hover:bg-[var(--accent)]/60'
            }`} />

            {/* Subtle center grip notch */}
            <div className={`absolute top-1/2 -translate-y-1/2 w-[2.5px] h-5 rounded-full transition-all duration-150 pointer-events-none ${
              isResizing 
                ? 'bg-[var(--accent)] opacity-100 scale-110' 
                : 'bg-[var(--border-color)] group-hover:bg-[var(--accent)] opacity-0 group-hover:opacity-80'
            }`} />
          </div>
        )}
      </aside>
    </div>
  </>
  );
};