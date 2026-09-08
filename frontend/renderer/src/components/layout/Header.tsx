import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { ThemeToggle } from '../ui/ThemeToggle';
import { IconMaximize, IconMinimize, IconClose } from '../ui/Icons';
import { RuexisLogo } from '../ui/RuexisLogo';
import { APP_BRANDING } from '../../constants/branding';

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
  const {
    togglePanel,
    uploadedFileName,
    activePaperId,
    activeConversationId,
    activeConversationTitle,
    conversations = [],
    uploadedHistory = [],
    messages = [],
    resetAnalysis,
  } = usePanelStore();

  const hasMessages = Array.isArray(messages) && messages.length > 0;
  const hasDocument = Boolean(uploadedFileName || activePaperId);

  // Find the active conversation
  const activeConv = conversations.find(
    (c) => (c.conversation_id || (c as any).id) === activeConversationId
  );

  // Resolve current candidate title: activeConversationTitle > activeConv.title > localStorage
  const storedTitle = typeof localStorage !== 'undefined' ? localStorage.getItem('active_conversation_title') : null;
  const candidateTitle = activeConversationTitle || activeConv?.title || storedTitle || '';
  const isGenericOrId = !candidateTitle || candidateTitle.startsWith('conv_') || candidateTitle === 'New Research Analysis' || candidateTitle === 'Research Thread' || candidateTitle === 'Untitled Thread';

  // Only consider conversation open if there are messages, or a document is loaded, or a real human title exists
  const isConversationOpen = (hasMessages || hasDocument || !isGenericOrId) && Boolean(activeConversationId || activeConversationTitle || hasDocument);

  let conversationTitle = '';
  if (isConversationOpen) {
    const cleanConvTitle = candidateTitle.replace(/^(Ingestion|Analysis|Mock Analysis):\s*/i, '').trim();

    const linkedPaperId = activeConv?.project_id || activePaperId;
    const paper = uploadedHistory.find(
      (h) => (linkedPaperId && h.id === linkedPaperId) ||
             (activeConv?.project_id && h.id === activeConv.project_id) ||
             (activePaperId && h.id === activePaperId) ||
             h.name === cleanConvTitle ||
             h.name === `${cleanConvTitle}.pdf` ||
             (cleanConvTitle.endsWith('.pdf') && h.name === cleanConvTitle)
    );
    const hasRealTitle = !!(paper?.title && paper.title !== paper.name && !paper.title.toLowerCase().endsWith('.pdf'));
    const isGeneric = !cleanConvTitle || 
      cleanConvTitle.startsWith('conv_') || 
      cleanConvTitle === 'New Research Analysis' || 
      cleanConvTitle === 'Research Thread' || 
      cleanConvTitle === 'Untitled Thread' ||
      cleanConvTitle.toLowerCase().endsWith('.pdf');

    if (!isGeneric) {
      // Prioritize the ChatGPT / Claude-style specific conversation title
      conversationTitle = cleanConvTitle;
    } else if (hasRealTitle && paper?.title) {
      conversationTitle = paper.title;
    } else if (uploadedFileName) {
      conversationTitle = uploadedFileName.replace(/\.(pdf|docx)$/i, '');
    } else if (paper?.name) {
      conversationTitle = paper.name.replace(/\.(pdf|docx)$/i, '');
    } else if (activePaperId) {
      conversationTitle = activePaperId.startsWith('paper_') ? activePaperId.substring(6) : activePaperId;
    }
  }

  // Never allow raw conv_ IDs or generic fallback strings to leak into the top bar
  if (!conversationTitle || conversationTitle.startsWith('conv_') || conversationTitle === 'Research Thread' || conversationTitle === 'New Research Analysis') {
    conversationTitle = '';
  }

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

  const displayTitle = isConversationOpen && conversationTitle
    ? conversationTitle
    : APP_BRANDING.NAME;

  return (
    <header className="h-12 app-rail flex items-center justify-between px-4 shrink-0 z-40 transition-colors border-none select-none">
      {/* ── Left: Logo + Current Conversation Title or Brand Name ── */}
      <div className="flex items-center gap-2.5 min-w-0">
        {/* Logo Mark */}
        <div 
          onClick={() => {
            if (isConversationOpen) {
              resetAnalysis();
            }
          }}
          className="w-7 h-7 rounded-lg flex items-center justify-center cursor-pointer hover:scale-105 transition-transform shrink-0 border app-border bg-[var(--bg-card)] shadow-xs" 
          data-tooltip={isConversationOpen ? `Return to ${APP_BRANDING.NAME}` : APP_BRANDING.NAME}
          data-tooltip-pos="bottom"
        >
          <RuexisLogo size={21} showBackground={false} />
        </div>

        {/* Single Constant Project Title */}
        <span 
          className="font-heading font-bold text-sm tracking-tight text-[var(--text-main)] select-none cursor-pointer"
          onClick={() => {
            if (isConversationOpen) {
              resetAnalysis();
            }
          }}
          data-tooltip={isConversationOpen ? `Return to ${APP_BRANDING.NAME}` : APP_BRANDING.TAGLINE}
          data-tooltip-pos="bottom"
        >
          {APP_BRANDING.NAME}
        </span>

        {/* Stable Conversation Title (set once per conversation thread, never re-fetched on every prompt) */}
        {isConversationOpen && conversationTitle && (
          <div className="flex items-center gap-2 min-w-0 animate-fade-in">
            <span className="w-px h-4 bg-[var(--border-color)] opacity-50 shrink-0" />
            <span className="w-2 h-2 rounded-full bg-[var(--accent)] shrink-0 animate-pulse" />
            <span 
              className="font-heading font-medium text-xs text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors truncate max-w-xs sm:max-w-md select-text"
              data-tooltip={conversationTitle}
              data-tooltip-pos="bottom"
            >
              {conversationTitle}
            </span>
          </div>
        )}
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
            data-tooltip={isMaximized ? "Minimize Screen" : "Maximize Screen"} 
            data-tooltip-pos="bottom"
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
            data-tooltip="Close Window" 
            data-tooltip-pos="bottom"
            className="w-6.5 h-6.5 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-red-500/80 hover:text-white transition-all cursor-pointer active:scale-95"
          >
            <IconClose className="text-xs" />
          </button>
        </div>
      </div>
    </header>
  );
};