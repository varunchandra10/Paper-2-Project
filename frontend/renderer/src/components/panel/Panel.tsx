import React, { useRef, useState, useCallback, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { Header } from '../layout/Header';
import { LeftSidebar } from '../layout/LeftSidebar';
import { RightSidebar } from '../layout/RightSidebar';
import { MascotBox } from '../layout/MascotBox';
import { MessageFeed } from '../features/chat/MessageFeed';
import { ChatInputArea } from '../features/chat/ChatInputArea';
import { LogsDrawer } from '../features/logs/LogsDrawer';
import { DocumentsDrawer } from '../features/analysis/DocumentsDrawer';
import { LocalAuthModal } from '../ui/LocalAuthModal';
import { UserProfile } from '../features/profile/UserProfile';
import { DragDropOverlay } from '../ui/DragDropOverlay';
import { PdfViewerPage } from '../features/analysis/PdfViewerPage';
import { APP_BRANDING } from '../../constants/branding';

interface StagedFile {
  filename: string;
  file: File;
  type: 'pdf' | 'docx';
}

export const Panel: React.FC = () => {
  const [isMaximized, setIsMaximized] = useState(false);
  // Keep sidebar closed by default on minimized screens until user opens it
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatInputValue, setChatInputValue] = useState('');
  const [stagedFile, setStagedFile] = useState<StagedFile | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Hidden file input ref & scroll container ref
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { 
    isPanelOpen, 
    uploadPaper, 
    sendMessage, 
    resetAnalysis, 
    activeView, 
    initIpcListeners,
    messages,
    isChatGenerating 
  } = usePanelStore();

  // ── Initialize Electron IPC listeners on mount ──
  useEffect(() => {
    initIpcListeners();

    // Sync maximize changes from Electron (if running inside Electron)
    if (window.mascotAPI?.onMaximizeChange) {
      window.mascotAPI.onMaximizeChange((maximized: boolean) => {
        setIsMaximized(maximized);
        setIsSidebarOpen(maximized ? true : false);
      });
    }
  }, [initIpcListeners]);

  // ── Rehydrate conversations, papers, profile & active thread on mount and window focus ──
  useEffect(() => {
    const syncData = () => {
      const state = usePanelStore.getState();
      state.fetchProfile();
      state.fetchConversations();
      state.fetchUploadedPapers();
      // Send stored mascot skin to Electron overlay
      const currentSkin = state.avatarId || (typeof localStorage !== 'undefined' ? localStorage.getItem('local_avatar_id') : null) || 'mr-nerdy';
      if (typeof window !== 'undefined' && window.mascotAPI?.setMascotSkin) {
        window.mascotAPI.setMascotSkin(currentSkin);
      }
    };

    syncData();

    // Re-sync seamlessly whenever window gains focus (e.g. after user restarts backend in terminal)
    window.addEventListener('focus', syncData);
    return () => window.removeEventListener('focus', syncData);
  }, []);

  // ── Auto-scroll full-height container to bottom on new messages ──
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, isChatGenerating]);

  // ── Sync thinking pose during ReAct chat generation ──
  useEffect(() => {
    if (isChatGenerating) {
      window.mascotAPI?.setMascotState?.('thinking');
    } else {
      window.mascotAPI?.setMascotState?.('idle');
    }
  }, [isChatGenerating]);

  // ── Report user activity to reset mascot idle / boredom timers ──
  useEffect(() => {
    let lastReport = 0;
    const handleActivity = () => {
      const now = Date.now();
      if (now - lastReport > 2000) {
        lastReport = now;
        window.mascotAPI?.reportUserActivity?.();
      }
    };

    window.addEventListener('mousemove', handleActivity, { passive: true });
    window.addEventListener('keydown', handleActivity, { passive: true });
    window.addEventListener('click', handleActivity, { passive: true });

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, []);

  // ── Maximize toggle ──
  const handleToggleMaximize = () => {
    setIsMaximized((prev) => {
      const next = !prev;
      // Default to open for full-screen maximized, closed for minimized
      setIsSidebarOpen(next ? true : false);
      return next;
    });
  };

  // ── File picker trigger ──
  const handleBrowseFile = () => {
    fileInputRef.current?.click();
  };

  // ── User picks a file via input ──
  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    processFile(file);
    e.target.value = '';
  };

  // ── Helper to stage & initiate upload ──
  const processFile = (file: File) => {
    const isDocx = file.name.endsWith('.docx');
    setStagedFile({ 
      filename: file.name, 
      file, 
      type: isDocx ? 'docx' : 'pdf' 
    });
    window.mascotAPI?.setMascotState?.('catching');
    uploadPaper(file);
  };

  // ── Global Panel Drag & Drop Handlers ──
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  }, [isDragging]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only turn off if leaving main boundary
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      processFile(droppedFile);
    }
  }, []);

  // ── User hits Send ──
  const handleSend = (message: string) => {
    if (message) {
      sendMessage(message, stagedFile !== null);
    }
    setChatInputValue('');
    setStagedFile(null);
  };

  if (!isPanelOpen) return null;

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="relative w-full h-full flex flex-col bg-[var(--bg-rail)] text-[var(--text-main)] font-sans overflow-hidden select-none transition-colors duration-300"
    >
      {/* Hidden browser-native file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleFileSelected}
      />

      {/* ── Drag & Drop Active Backdrop Overlay ── */}
      <DragDropOverlay isDragging={isDragging} />

      {/* ── FULL-WIDTH TOP HEADER (seamless inverted L-frame) ── */}
      <Header
        isMaximized={isMaximized}
        handleToggleMaximize={handleToggleMaximize}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* ── BELOW HEADER: RAIL + SIDEBAR + MAIN (seamless L-frame flex-row) ── */}
      <div className="flex flex-1 overflow-hidden app-rail">
        {/* Left Sidebar (Slim Icon Rail + Expanded Papers Drawer) */}
        <LeftSidebar 
          isMaximized={isMaximized} 
          isOpen={isSidebarOpen} 
          onToggleOpen={() => setIsSidebarOpen((prev) => !prev)}
        />

        {/* ── CENTER MAIN CONTENT CONTAINER (Floating Editor Panel - No Top Gap) ── */}
        <main className="flex-1 flex flex-col overflow-hidden overflow-x-hidden bg-[var(--bg-base)] mb-1.5 mr-1.5 rounded-xl border app-border shadow-xs transition-colors relative min-w-0 max-w-full">
          {activeView === 'profile' ? (
            <UserProfile />
          ) : activeView === 'pdf-viewer' ? (
            <PdfViewerPage />
          ) : (
            <div 
              ref={scrollRef}
              className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-[var(--text-muted)]/30 scrollbar-track-transparent relative w-full max-w-full flex flex-col justify-between"
            >
              {/* Conversation Stream */}
              <MessageFeed isMaximized={isMaximized} />

              {/* Sticky Floating Bottom Area (Input Dock + Claude Footer) */}
              <div className="sticky bottom-0 z-20 w-full flex flex-col items-center bg-gradient-to-t from-[var(--bg-base)] via-[var(--bg-base)]/95 to-transparent pt-4 pb-2 px-4 shrink-0">
                <ChatInputArea
                  isMaximized={isMaximized}
                  chatInputValue={chatInputValue}
                  setChatInputValue={setChatInputValue}
                  handleBrowseFile={handleBrowseFile}
                  stagedFile={stagedFile ? { filename: stagedFile.filename, filePath: '', type: stagedFile.type } : null}
                  onClearStagedFile={() => { setStagedFile(null); resetAnalysis(); }}
                  onSend={handleSend}
                />

                {/* Claude-style Footer Disclaimer */}
                <div className={`w-full max-w-[800px] pt-1 pb-1 flex items-center justify-between text-[var(--text-muted)] font-sans ${
                  isMaximized 
                    ? 'px-6 text-[11px]' 
                    : 'px-1 text-[8px] leading-tight'
                }`}>
                  <span className={isMaximized ? '' : 'truncate mr-2'}>
                    {APP_BRANDING.LATENCY_NOTICE}
                  </span>
                  <button 
                    onClick={() => usePanelStore.getState().toggleLogs()} 
                    className={`underline underline-offset-2 hover:text-[var(--text-main)] transition-colors cursor-pointer font-mono shrink-0 ${
                      isMaximized ? 'text-[10px]' : 'text-[8px]'
                    }`}
                  >
                    Terminal
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── BOTTOM-LEFT CORNER MASCOT COMPANION DOCK (Maximized Full-Screen Mode Only) ── */}
          {isMaximized && !isSidebarOpen && activeView === 'chat' && (
            <div className="absolute bottom-5 left-5 z-30 hidden sm:block animate-fade-in pointer-events-auto">
              <MascotBox isOpen={true} isMaximized={isMaximized} />
            </div>
          )}

          {/* Slide-Up Drawers */}
          <LogsDrawer />
          {!isMaximized && <DocumentsDrawer />}
        </main>

        {/* Right Sidebar (Documents history pane) */}
        <RightSidebar isMaximized={isMaximized} />
      </div>

      {/* Authentication / Onboarding Modal */}
      <LocalAuthModal />
    </div>
  );
};