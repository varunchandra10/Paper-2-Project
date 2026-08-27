import React, { useRef, useState, useCallback } from 'react';
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
import { FiUploadCloud } from 'react-icons/fi';

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

  // Hidden file input ref — browser-native file picker
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { isPanelOpen, uploadPaper, sendMessage, resetAnalysis, activeView } = usePanelStore();

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
      sendMessage(message);
    }
    setChatInputValue('');
  };

  if (!isPanelOpen) return null;

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="relative w-full h-full flex bg-background text-foreground font-sans overflow-hidden select-none transition-colors duration-300"
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
      {isDragging && (
        <div className="absolute inset-0 z-50 bg-background/90 backdrop-blur-md border-2 border-dashed border-brass/60 flex flex-col items-center justify-center gap-3 animate-fade-in pointer-events-none">
          <div className="w-16 h-16 rounded-2xl bg-brass/10 border border-brass/40 flex items-center justify-center text-brass shadow-[0_0_20px_rgba(212,175,55,0.2)] animate-bounce">
            <FiUploadCloud className="text-3xl" />
          </div>
          <div className="flex flex-col items-center gap-1">
            <span className="text-sm font-bold font-mono text-foreground tracking-wide">
              Drop Document Here
            </span>
            <span className="text-xs font-mono text-muted-foreground">
              Supports PDF and DOCX analysis
            </span>
          </div>
        </div>
      )}

      {/* 1. Left Sidebar (Maximized mode view) */}
      <LeftSidebar isMaximized={isMaximized} isOpen={isSidebarOpen} />

      {/* 2. Main Viewport Workspace */}
      <section className="flex-1 h-full flex flex-col overflow-hidden relative min-w-0 bg-gradient-to-b from-transparent via-background/50 to-background/90">
        
        {/* Top Navigation Header */}
        <Header
          isMaximized={isMaximized}
          handleToggleMaximize={handleToggleMaximize}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        />

        {activeView === 'profile' ? (
          <UserProfile />
        ) : (
          <>
            {/* Conversation Stream */}
            <MessageFeed isMaximized={isMaximized} />

            {/* Input Dock Area */}
            <ChatInputArea
              isMaximized={isMaximized}
              chatInputValue={chatInputValue}
              setChatInputValue={setChatInputValue}
              handleBrowseFile={handleBrowseFile}
              stagedFile={stagedFile ? { filename: stagedFile.filename, filePath: '', type: stagedFile.type } : null}
              onClearStagedFile={() => { setStagedFile(null); resetAnalysis(); }}
              onSend={handleSend}
            />
          </>
        )}

        {/* Slide-Up Drawers */}
        <LogsDrawer />
        {!isMaximized && <DocumentsDrawer />}
      </section>

      {/* 3. Right Sidebar (Maximized documents history pane) */}
      <RightSidebar isMaximized={isMaximized} />

      {/* Authentication / Onboarding Modal */}
      <LocalAuthModal />
    </div>
  );
};