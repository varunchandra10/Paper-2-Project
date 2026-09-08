import React, { useEffect, useState, useRef } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { SkinLoader } from '../ui/SkinLoader';
import { IconMessageSquare, IconTrash, IconMoreHorizontal, IconEdit, IconCheck, IconClose } from '../ui/Icons';

export const ChatHistoryList: React.FC<{ isOpen: boolean; onSelect?: () => void }> = ({ isOpen, onSelect }) => {
  const {
    conversations = [],
    activeConversationId,
    fetchConversations,
    selectConversation,
    deleteConversation,
    updateConversationTitle,
    isConversationsLoading,
    uploadedHistory = [],
    fetchUploadedPapers,
    userId
  } = usePanelStore();

  const [menuOpenConvId, setMenuOpenConvId] = useState<string | null>(null);
  const [editingConvId, setEditingConvId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchConversations();
    fetchUploadedPapers();
  }, [fetchConversations, fetchUploadedPapers, userId]);

  // Click outside listener to dismiss the three-dots dropdown
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpenConvId(null);
      }
    };
    if (menuOpenConvId) {
      document.addEventListener('pointerdown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('pointerdown', handleOutsideClick);
    };
  }, [menuOpenConvId]);

  const handleStartRename = (convId: string, currentTitle: string) => {
    setMenuOpenConvId(null);
    setEditingConvId(convId);
    setEditTitle(currentTitle);
  };

  const handleSaveRename = (convId: string) => {
    const trimmed = editTitle.trim();
    if (trimmed) {
      updateConversationTitle(convId, trimmed);
    }
    setEditingConvId(null);
  };

  if (!isOpen) return null;

  /* Expanded Sidebar Drawer View */
  return (
    <div className="flex-1 flex flex-col min-h-0 pt-2 pb-1 overflow-hidden select-none">
      {/* Scrollable Conversation List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent px-2.5 space-y-1 pr-1.5 w-full max-w-full">
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
            const isEditing = editingConvId === convId;
            const isMenuOpen = menuOpenConvId === convId;

            // Title Resolution (ChatGPT & Claude style):
            // Priority: Real Conversation Title -> Fallback to Paper Title -> Fallback to PDF name
            const rawTitle = conv.title || '';
            const cleanRaw = rawTitle.replace(/^(Ingestion|Analysis|Mock Analysis):\s*/i, '').trim();

            const isGeneric = !cleanRaw || 
              cleanRaw.startsWith('conv_') || 
              cleanRaw === 'New Research Analysis' || 
              cleanRaw === 'Research Thread' || 
              cleanRaw === 'Untitled Thread' ||
              cleanRaw.toLowerCase().endsWith('.pdf');

            let cleanTitle = cleanRaw || 'Untitled Thread';
            if (isGeneric) {
              const paper = uploadedHistory.find(
                (h) => (conv.project_id && h.id === conv.project_id) ||
                       h.name === cleanRaw ||
                       h.name === `${cleanRaw}.pdf`
              );
              cleanTitle = paper?.title || paper?.name?.replace(/\.(pdf|docx)$/i, '') || 'Research Analysis';
            }

            return (
              <div
                key={convId}
                onClick={() => {
                  if (!isEditing) {
                    selectConversation(convId);
                    if (onSelect) onSelect();
                  }
                }}
                className={`group relative flex items-center justify-between p-2 rounded-xl text-left transition-all duration-150 cursor-pointer border ${
                  isActive
                    ? 'bg-[var(--accent-subtle)] border-[var(--accent)] text-[var(--accent)] font-semibold shadow-xs'
                    : 'bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] border-[var(--border-color)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
                }`}
              >
                {/* Thread Icon & Title (or Inline Edit Input) */}
                <div className="flex items-center gap-2 min-w-0 flex-1 pr-1">
                  <IconMessageSquare
                    className={`text-xs shrink-0 transition-colors ${
                      isActive ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] group-hover:text-[var(--accent)]'
                    }`}
                  />

                  {isEditing ? (
                    <div
                      className="flex items-center gap-1 flex-1 min-w-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveRename(convId);
                          if (e.key === 'Escape') setEditingConvId(null);
                        }}
                        autoFocus
                        className="flex-1 min-w-0 bg-[var(--bg-base)] border border-[var(--accent)] text-[var(--text-main)] text-xs rounded-lg px-2 py-0.5 outline-none font-sans font-normal shadow-inner"
                      />
                      <button
                        type="button"
                        onClick={() => handleSaveRename(convId)}
                        data-tooltip="Save name (Enter)"
                        className="p-1 rounded-md text-emerald-400 hover:bg-emerald-400/10 cursor-pointer shrink-0 transition-colors"
                      >
                        <IconCheck className="text-xs" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingConvId(null)}
                        data-tooltip="Cancel (Esc)"
                        className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] cursor-pointer shrink-0 transition-colors"
                      >
                        <IconClose className="text-xs" />
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs font-sans truncate leading-snug">
                      {cleanTitle}
                    </span>
                  )}
                </div>

                {/* Horizontal Three Dots Menu Button */}
                {!isEditing && (
                  <div
                    className="relative shrink-0"
                    ref={isMenuOpen ? menuRef : null}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpenConvId(isMenuOpen ? null : convId);
                      }}
                      data-tooltip="Thread options"
                      data-tooltip-pos="left"
                      className={`p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-all duration-150 cursor-pointer outline-none ${
                        isMenuOpen ? 'opacity-100 bg-[var(--accent-subtle)] text-[var(--text-main)]' : 'opacity-0 group-hover:opacity-100'
                      }`}
                    >
                      <IconMoreHorizontal className="text-xs" />
                    </button>

                    {/* Popover Dropdown */}
                    {isMenuOpen && (
                      <div className="absolute right-0 top-full mt-1 w-28 rounded-xl bg-[var(--bg-card)] border app-border shadow-xl p-1 z-50 animate-fade-in flex flex-col gap-0.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(convId, cleanTitle);
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-[var(--text-main)] hover:bg-[var(--accent-subtle)] hover:text-[var(--accent)] rounded-lg transition-colors text-left cursor-pointer"
                        >
                          <IconEdit className="text-xs text-[var(--accent)]" />
                          <span>Rename</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setMenuOpenConvId(null);
                            deleteConversation(convId);
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-red-400 hover:bg-red-400/10 rounded-lg transition-colors text-left cursor-pointer"
                        >
                          <IconTrash className="text-xs" />
                          <span>Delete</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};