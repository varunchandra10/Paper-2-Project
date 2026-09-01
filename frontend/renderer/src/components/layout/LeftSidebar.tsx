import React, { useState } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { ChatHistoryList } from './ChatHistoryList';
import { DocumentHistoryList } from './DocumentHistoryList';
import { SkinLoader } from '../ui/SkinLoader';
import { 
  IconMessageSquare, 
  IconBookOpen, 
  IconActivity,
  IconPlus
} from '../ui/Icons';

interface LeftSidebarProps {
  isMaximized: boolean;
  isOpen: boolean;
  onToggleOpen?: () => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({ isOpen, onToggleOpen }) => {
  const { 
    resetAnalysis, 
    setActiveView,
    fetchConversations,
    hardwareMetrics,
    fetchHardwareMetrics,
    isHardwareLoading
  } = usePanelStore();
  const [activeTab, setActiveTab] = useState<'chat' | 'library' | 'feasibility'>('chat');

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
    if (!isOpen && onToggleOpen) {
      onToggleOpen();
    }
  };

  return (
    <div className="flex h-full shrink-0 z-30 select-none">
      {/* ── 1. VS CODE ACTIVITY BAR (Slim Icon Rail) ── */}
      <aside className="w-12 app-rail flex flex-col items-center justify-between py-2 shrink-0 transition-colors">
        <div className="flex flex-col items-center gap-4 w-full">
          {/* Navigation Icons with Rounded Pill Hover & Active Border Styling */}
          <nav className="flex flex-col gap-2 w-full items-center">
            {/* New Conversation Plus Button */}
            <button
              onClick={handleNewConversation}
              className="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer text-[var(--accent)] bg-[var(--accent-subtle)] border border-[var(--accent-border)] hover:scale-105 active:scale-95 shadow-xs mb-1"
              title="New Research Conversation"
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
              title="Conversational History"
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
              title="Document History"
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
              title="Hardware Radar"
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
            title={isOpen ? 'Hide Primary Side Bar' : 'Show Primary Side Bar'}
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
            title="User Profile"
          >
            VC
          </button>
        </div>
      </aside>

      {/* ── 2. VS CODE EXPLORER PANEL (Rounded Card Panel) ── */}
      <aside
        className={`bg-[var(--bg-sidebar)] border app-border rounded-xl shadow-xs flex flex-col justify-between shrink-0 transition-all duration-300 ease-in-out overflow-hidden mb-1.5 ${
          isOpen ? 'w-60 opacity-100 mr-1.5' : 'w-0 opacity-0 border-none p-0 pointer-events-none'
        }`}
      >
        <div className="w-[240px] flex flex-col h-full overflow-hidden shrink-0">
          
          {/* Top Panel Title Header Bar */}
          <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b app-border select-none">
            <span className="text-[11px] font-sans font-bold tracking-wider text-[var(--text-muted)] uppercase">
              {activeTab === 'chat' ? 'CHAT HISTORY' : activeTab === 'library' ? 'DOCUMENT HISTORY' : 'HARDWARE RADAR'}
            </span>
          </div>

          {/* Render ChatHistoryList component when Chat tab is active */}
          {activeTab === 'chat' && (
            <ChatHistoryList isOpen={isOpen} />
          )}

          {/* Render DocumentHistoryList component when Document History (Library) tab is active */}
          {activeTab === 'library' && (
            <DocumentHistoryList isOpen={isOpen} />
          )}

          {/* Render Live Hardware Radar when Feasibility tab is active */}
          {activeTab === 'feasibility' && (
            <div className="p-2.5 font-mono space-y-2 overflow-y-auto flex-1 text-[10px]">
              <div className="flex items-center justify-between border-b app-border pb-1">
                <span className="font-bold text-[var(--accent)] text-[10px] tracking-wider">HARDWARE RADAR</span>
                <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold ${
                  isHardwareLoading 
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] animate-pulse' 
                    : 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
                }`}>
                  {isHardwareLoading ? 'PROBING METRICS...' : (hardwareMetrics?.status?.toUpperCase() || 'ONLINE')}
                </span>
              </div>

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

        </div>
      </aside>
    </div>
  );
};