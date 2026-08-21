import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { useLogsStore } from '../../store/logsStore';
import { Header } from '../layout/Header';
import { LeftSidebar } from '../layout/LeftSidebar';
import { RightSidebar } from '../layout/RightSidebar';
import { MessageFeed } from '../features/chat/MessageFeed';
import { ChatInputArea } from '../features/chat/ChatInputArea';
import { LogsDrawer } from '../features/logs/LogsDrawer';
import { DocumentsDrawer } from '../features/analysis/DocumentsDrawer';

export const Panel: React.FC = () => {
  const [isMaximized, setIsMaximized] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);
  const [chatInputValue, setChatInputValue] = React.useState('');

  const { isPanelOpen, selectedModel } = usePanelStore();

  React.useEffect(() => {
    if (window.mascotAPI?.onMaximizeChange) {
      window.mascotAPI.onMaximizeChange((maximized) => {
        setIsMaximized(maximized);
        // Reset sidebar to open whenever we enter maximized mode
        if (maximized) setIsSidebarOpen(true);
      });
    }

    if (window.mascotAPI?.onUploadStatus) {
      window.mascotAPI.onUploadStatus((status) => {
        if (status.success) {
          usePanelStore.getState().startAnalysis(status.filename, status.type);
        } else {
          const { addLog } = useLogsStore.getState();
          addLog(`[Error] Ingestion failed: ${status.error}`, 'error');
        }
      });
    }

    if (window.mascotAPI?.onPipelineLog) {
      window.mascotAPI.onPipelineLog((log) => {
        const { addLog } = useLogsStore.getState();
        const logText = log.text;
        let type: 'info' | 'success' | 'warning' | 'error' | 'system' = 'info';

        if (logText.includes('[Success]')) type = 'success';
        else if (logText.includes('[System]')) type = 'system';
        else if (logText.includes('[Error]')) type = 'error';
        else if (logText.includes('[Warning]')) type = 'warning';

        addLog(logText, type);

        if (logText.includes('Step 1')) usePanelStore.getState().setMilestoneActive(0);
        else if (logText.includes('Step 2')) usePanelStore.getState().setMilestoneActive(1);
        else if (logText.includes('Step 3')) usePanelStore.getState().setMilestoneActive(2);
        else if (logText.includes('Step 4')) usePanelStore.getState().setMilestoneActive(3);
        else if (logText.includes('Step 5')) usePanelStore.getState().setMilestoneActive(4);
      });
    }

    if (window.mascotAPI?.onPipelineCompleted) {
      window.mascotAPI.onPipelineCompleted((result) => {
        if (result.success && result.reportContent) {
          usePanelStore.getState().completeAnalysis(result.reportContent);
        } else {
          usePanelStore.getState().failAnalysis(result.error || 'Pipeline execution failed');
        }
      });
    }
  }, []);

  const handleToggleMaximize = () => {
    if (window.mascotAPI?.toggleMaximize) {
      window.mascotAPI.toggleMaximize();
    } else {
      setIsMaximized(!isMaximized);
    }
  };

  const handleBrowseFile = () => {
    if (window.mascotAPI?.openFileSelector) {
      window.mascotAPI.openFileSelector('pdf', selectedModel);
    }
  };

  if (!isPanelOpen) return null;

  return (
    <div className="relative w-full h-full flex bg-background text-foreground font-sans overflow-hidden select-none border border-border/55 animate-fade-in">
      {/* 1. Left Sidebar (Maximized mode only, collapsible via ham menu) */}
      <LeftSidebar isMaximized={isMaximized} isOpen={isSidebarOpen} />

      {/* 2. Main Viewport Container */}
      <section className="flex-1 h-full flex flex-col overflow-hidden relative min-w-0">
        {/* Top Header */}
        <Header
          isMaximized={isMaximized}
          handleToggleMaximize={handleToggleMaximize}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
        />

        {/* Message Feed (Chat Viewport) */}
        <MessageFeed isMaximized={isMaximized} />

        {/* Chat Input Footer Area */}
        <ChatInputArea
          isMaximized={isMaximized}
          chatInputValue={chatInputValue}
          setChatInputValue={setChatInputValue}
          handleBrowseFile={handleBrowseFile}
        />

        {/* Slide-Up System Console / Ingestion Drawer */}
        <LogsDrawer />
        {!isMaximized && <DocumentsDrawer />}
      </section>

      {/* 3. Right Sidebar (Maximized documents history pane) */}
      <RightSidebar isMaximized={isMaximized} />
    </div>
  );
};