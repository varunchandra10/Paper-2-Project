import React, { useRef, useState, useCallback, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { Header } from '../layout/Header';
import { LeftSidebar } from '../layout/LeftSidebar';
import { RightSidebar } from '../layout/RightSidebar';
import { MessageFeed } from '../features/chat/MessageFeed';
import { ChatInputArea } from '../features/chat/ChatInputArea';
import { LogsDrawer } from '../features/logs/LogsDrawer';
import { DocumentsDrawer } from '../features/analysis/DocumentsDrawer';
import { LocalAuthModal } from '../ui/LocalAuthModal';
import { UserProfile } from '../features/profile/UserProfile';
import { DragDropOverlay } from '../ui/DragDropOverlay';
import { PdfViewerPage } from '../features/analysis/PdfViewerPage';

interface StagedFile {
  filename: string;
  file: File;
  type: 'pdf' | 'docx';
}

export const Panel: React.FC = () => {
  const [isMaximized, setIsMaximized] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
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
  }, [initIpcListeners]);

  // ── Auto-scroll full-height container to bottom on new messages ──
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, isChatGenerating]);

  // ── Maximize toggle ──
  const handleToggleMaximize = () => {
    setIsMaximized((prev) => {
      if (!prev) setIsSidebarOpen(true);
      return !prev;
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
        <main className="flex-1 flex flex-col overflow-hidden bg-[var(--bg-base)] mb-1.5 mr-1.5 rounded-xl border app-border shadow-xs transition-colors relative min-w-0">
          {activeView === 'profile' ? (
            <UserProfile />
          ) : activeView === 'pdf-viewer' ? (
            <PdfViewerPage />
          ) : (
            <div 
              ref={scrollRef}
              className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-[var(--text-muted)]/30 scrollbar-track-transparent relative w-full flex flex-col justify-between"
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
                <div className="w-full max-w-[800px] px-6 pt-1 pb-1 flex items-center justify-between text-[11px] text-[var(--text-muted)] font-sans">
                  <span>Synthexis runs on free local models; apologies for any latency</span>
                  <button 
                    onClick={() => usePanelStore.getState().toggleLogs()} 
                    className="underline underline-offset-2 hover:text-[var(--text-main)] transition-colors cursor-pointer font-mono text-[10px]"
                  >
                    Terminal Logs
                  </button>
                </div>
              </div>
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