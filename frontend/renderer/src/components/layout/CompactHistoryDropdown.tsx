import React, { useEffect, useRef } from 'react';
import { FiClock, FiMessageSquare, FiChevronRight } from 'react-icons/fi';
import { usePanelStore } from '../../store/panelStore';

interface CompactHistoryDropdownProps {
  onClose: () => void;
}

export const CompactHistoryDropdown: React.FC<CompactHistoryDropdownProps> = ({ onClose }) => {
  const { 
    conversations, 
    activeConversationId, 
    selectConversation, 
    setActiveView 
  } = usePanelStore();

  const dropdownRef = useRef<HTMLDivElement>(null);

  /* Click outside and Escape key handler */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  return (
    <div 
      ref={dropdownRef}
      className="absolute right-0 top-9 w-72 bg-[var(--bg-card)] border app-border rounded-2xl shadow-[0_16px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl p-2.5 z-50 animate-fade-in flex flex-col gap-1.5 max-h-80 overflow-hidden select-none text-[var(--text-main)]"
    >
      {/* HUD Accent Corner Brackets */}
      <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-[var(--accent-border)] pointer-events-none" />
      <div className="absolute top-2 right-2 w-2 h-2 border-t border-r border-[var(--accent-border)] pointer-events-none" />
      <div className="absolute bottom-2 left-2 w-2 h-2 border-b border-l border-[var(--accent-border)] pointer-events-none" />
      <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-[var(--accent-border)] pointer-events-none" />

      {/* Dropdown Header */}
      <div className="px-2 py-1 flex items-center justify-between border-b app-border">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--accent)] flex items-center gap-1.5">
          <FiClock className="text-xs shrink-0" />
          <span>Research Threads</span>
        </span>
        <span className="text-[9px] font-mono text-[var(--accent)] font-bold px-1.5 py-0.5 rounded-md bg-[var(--accent-subtle)] border border-[var(--accent-border)]">
          {conversations.length} Threads
        </span>
      </div>

      {/* Conversation Thread List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent py-0.5 space-y-1 pr-0.5">
        {conversations.length === 0 ? (
          <div className="py-7 flex flex-col items-center justify-center text-center p-3 rounded-xl border border-dashed app-border bg-[var(--bg-base)]/50 my-1">
            <FiMessageSquare className="text-[var(--text-muted)] text-sm mb-1" />
            <span className="text-[10px] font-mono text-[var(--text-muted)]">No active research history</span>
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.conversation_id === activeConversationId;
            return (
              <button
                key={conv.conversation_id}
                onClick={async () => {
                  await selectConversation(conv.conversation_id);
                  setActiveView('chat');
                  onClose();
                }}
                className={`w-full flex items-center gap-2 p-2 rounded-xl text-left transition-all duration-150 cursor-pointer border group outline-none ${
                  isActive
                    ? 'bg-[var(--accent-subtle)] border-[var(--accent-border)] text-[var(--accent)] font-bold'
                    : 'bg-[var(--bg-base)]/50 hover:bg-[var(--accent-subtle)] border-transparent hover:border-[var(--accent-border)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
              >
                <FiMessageSquare className={`text-xs shrink-0 transition-colors ${
                  isActive ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] group-hover:text-[var(--accent)]'
                }`} />
                <span className="text-xs font-mono truncate leading-snug flex-1">
                  {conv.title}
                </span>
                <FiChevronRight className={`text-xs transition-transform duration-150 ${
                  isActive ? 'text-[var(--accent)] translate-x-0.5' : 'text-[var(--text-muted)] group-hover:text-[var(--accent)] group-hover:translate-x-0.5'
                }`} />
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};