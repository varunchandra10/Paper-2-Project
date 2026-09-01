import React, { useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { SkinLoader } from '../ui/SkinLoader';
import { IconMessageSquare, IconTrash, IconClock } from '../ui/Icons';

export const ChatHistoryList: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  const {
    conversations = [],
    activeConversationId,
    fetchConversations,
    selectConversation,
    deleteConversation,
    isConversationsLoading,
    userId
  } = usePanelStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, userId]);

  if (!isOpen) return null;

  /* Expanded Sidebar Drawer View */
  return (
    <div className="flex-1 flex flex-col min-h-0 py-2.5 overflow-hidden select-none">
      {/* Drawer Section Header */}
      <div className="px-3 pb-2 flex items-center justify-between shrink-0 font-sans">
        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
          <IconClock className="text-[var(--accent)] text-xs shrink-0" />
          <span>Research Threads</span>
        </div>
        <span className="text-[10px] font-mono text-[var(--accent)] font-semibold px-1.5 py-0.5 rounded-md bg-[var(--accent-subtle)] border border-[var(--accent)]/30">
          {conversations.length}
        </span>
      </div>

      {/* Scrollable Conversation List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent px-2.5 space-y-1 pr-1.5">
        {isConversationsLoading ? (
          <SkinLoader type="chat" />
        ) : conversations.length === 0 ? (
          <div className="py-8 flex flex-col items-center justify-center text-center p-3 rounded-xl border border-dashed app-border bg-[var(--bg-base)] font-sans">
            <IconMessageSquare className="text-[var(--text-muted)] text-base mb-1" />
            <span className="text-[11px] text-[var(--text-muted)]">No previous research threads</span>
          </div>
        ) : (
          conversations.map((conv, idx) => {
            const convId = conv.conversation_id || (conv as any).id || `conv-${idx}`;
            const isActive = convId === activeConversationId;
            return (
              <div
                key={convId}
                onClick={() => selectConversation(convId)}
                className={`group relative flex items-center justify-between p-2 rounded-xl text-left transition-all duration-150 cursor-pointer border ${
                  isActive
                    ? 'bg-[var(--accent-subtle)] border-[var(--accent)] text-[var(--accent)] font-semibold shadow-xs'
                    : 'bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] border-[var(--border-color)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1 pr-1">
                  <IconMessageSquare className={`text-xs shrink-0 transition-colors ${
                    isActive ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] group-hover:text-[var(--accent)]'
                  }`} />
                  <span className="text-xs font-sans truncate leading-snug">
                    {conv.title || 'Untitled Thread'}
                  </span>
                </div>

                {/* Delete Thread Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(convId);
                  }}
                  title="Delete chat thread"
                  className="opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-red-400 p-1 rounded-lg hover:bg-red-400/10 transition-all duration-150 cursor-pointer shrink-0 outline-none"
                >
                  <IconTrash className="text-xs" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};