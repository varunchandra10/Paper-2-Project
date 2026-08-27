import React, { useRef, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { ModelSelector } from '../../ui/ModelSelector';
import { 
  FiPlus, 
  FiFileText, 
  FiTerminal, 
  FiX, 
  FiFile, 
  FiArrowUp,
  FiCheckCircle,
  FiAlertCircle,
  FiLoader
} from 'react-icons/fi';

interface StagedFile {
  filename: string;
  filePath: string;
  type: 'pdf' | 'docx' | string;
  modelName?: string;
}

interface ChatInputAreaProps {
  isMaximized: boolean;
  chatInputValue: string;
  setChatInputValue: (val: string) => void;
  handleBrowseFile: () => void;
  stagedFile?: StagedFile | null;
  onClearStagedFile?: () => void;
  onSend?: (message: string) => void;
}

export const ChatInputArea: React.FC<ChatInputAreaProps> = ({
  isMaximized,
  chatInputValue,
  setChatInputValue,
  handleBrowseFile,
  stagedFile,
  onClearStagedFile,
  onSend,
}) => {
  const { 
    isHistoryOpen, 
    toggleHistory,
    isLogsOpen,
    toggleLogs,
    sendMessage,
    isAnalyzing,
    activeMilestoneIndex,
    analysisStatus
  } = usePanelStore();

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea logic
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [chatInputValue]);

  const canSend = !isAnalyzing && (!!stagedFile || !!chatInputValue.trim());

  const handleSubmit = () => {
    if (!canSend) return;
    const trimmed = chatInputValue.trim();
    if (onSend) {
      onSend(trimmed);
    } else if (trimmed) {
      sendMessage(trimmed);
    }
    setChatInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const progressPercent = isAnalyzing ? Math.min(95, (activeMilestoneIndex + 1) * 20) : 100;

  return (
    <footer className="px-4 pb-4 pt-2 z-20 shrink-0 bg-background/80 backdrop-blur-md">
      <div className="max-w-[800px] mx-auto flex flex-col gap-2">
        
        {/* Header Toolbar (Docs & Terminal toggles) */}
        {!isMaximized && (
          <div className="flex items-center gap-2 px-1 select-none">
            <button 
              onClick={toggleHistory}
              className={`group relative rounded-lg border transition-all duration-200 cursor-pointer flex items-center justify-center w-7 h-7 ${
                isHistoryOpen 
                  ? 'border-red-500/40 bg-red-500/10 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.15)]' 
                  : 'border-border/60 text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
              title="Documents & History"
            >
              <FiFileText className="text-xs transition-transform group-hover:scale-110" />
            </button>

            <button 
              onClick={toggleLogs}
              className={`group relative rounded-lg border transition-all duration-200 cursor-pointer flex items-center justify-center w-7 h-7 ${
                isLogsOpen 
                  ? 'border-amber-500/40 bg-amber-500/10 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.15)]' 
                  : 'border-border/60 text-muted-foreground hover:bg-accent hover:text-foreground'
              }`}
              title="Terminal Console"
            >
              <FiTerminal className="text-xs transition-transform group-hover:scale-110" />
            </button>
          </div>
        )}

        {/* Status Loader */}
        {isAnalyzing && (
          <div className="flex items-center gap-2 px-2 py-1 select-none text-[10px] font-mono text-brass font-semibold tracking-wide bg-brass/5 border border-brass/20 rounded-lg w-fit animate-pulse">
            <FiLoader className="w-3 h-3 animate-spin text-brass shrink-0" />
            <span>Processing document pipeline...</span>
          </div>
        )}

        {/* Chat Card Box — set overflow-visible to prevent clipping ModelSelector */}
        <div className="flex flex-col bg-card/90 border border-border/60 rounded-2xl shadow-xl relative overflow-visible transition-all duration-200 focus-within:border-brass/40 focus-within:ring-1 focus-within:ring-brass/30">

          {/* Staged File Chip & Status Badges */}
          {stagedFile && (
            <div className="px-3.5 pt-3 pb-1 select-none flex items-center gap-2 flex-wrap border-b border-border/30 bg-muted/20 rounded-t-2xl overflow-hidden">
              <div className="relative inline-flex items-center gap-2 rounded-lg bg-brass/10 border border-brass/30 text-brass text-[11px] font-mono font-medium px-2.5 py-1.5 max-w-full overflow-hidden shadow-sm">
                <FiFile className="shrink-0 text-xs" />
                <span className="truncate max-w-[240px]" title={stagedFile.filename}>
                  {stagedFile.filename}
                </span>

                {!isAnalyzing && onClearStagedFile && (
                  <button
                    onClick={onClearStagedFile}
                    className="ml-1 p-0.5 rounded-full hover:bg-brass/20 text-brass/70 hover:text-brass transition-colors shrink-0 cursor-pointer"
                    title="Remove file"
                  >
                    <FiX className="text-xs" />
                  </button>
                )}

                {/* Progress bar overlay during active analysis */}
                {isAnalyzing && (
                  <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-brass/20">
                    <div 
                      className="h-full bg-brass transition-all duration-500 ease-out shadow-[0_0_6px_rgba(212,175,55,0.8)]"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Status Badges */}
              {analysisStatus === 'success' && (
                <div className="inline-flex items-center gap-1.5 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold font-mono tracking-wider uppercase px-2.5 py-1 rounded-lg select-none shadow-sm shrink-0">
                  <FiCheckCircle className="text-xs" />
                  <span>Verified</span>
                </div>
              )}
              {analysisStatus === 'error' && (
                <div className="inline-flex items-center gap-1.5 bg-red-500/15 border border-red-500/30 text-red-400 text-[10px] font-bold font-mono tracking-wider uppercase px-2.5 py-1 rounded-lg select-none shadow-sm shrink-0">
                  <FiAlertCircle className="text-xs" />
                  <span>Ingestion Failed</span>
                </div>
              )}
            </div>
          )}

          {/* Dynamic Auto-Resizing Textarea */}
          <div className="px-3.5 pt-3 pb-1">
            <textarea 
              ref={textareaRef}
              rows={1}
              value={chatInputValue}
              onChange={(e) => setChatInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isAnalyzing}
              placeholder={
                isAnalyzing
                  ? "Analyzing document sections in background..."
                  : stagedFile
                  ? "Add query instructions or hit Send..."
                  : "Ask anything, @ to mention, / for actions"
              }
              className="w-full bg-transparent outline-none resize-none text-xs text-foreground placeholder:text-muted-foreground/60 font-sans leading-relaxed min-h-[42px] max-h-[180px] disabled:opacity-50"
            />
          </div>

          {/* Bottom Bar: Model Selector & Actions */}
          <div className="px-3 pb-2.5 pt-1 flex justify-between items-center select-none border-t border-transparent relative z-30">
            <div className="flex items-center gap-1.5">
              <button 
                onClick={handleBrowseFile}
                disabled={isAnalyzing}
                className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/80 rounded-lg transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed active:scale-95"
                title="Upload PDF/Document"
              >
                <FiPlus className="text-base" />
              </button>

              <div className="h-4 w-[1px] bg-border/40 mx-0.5" />

              <ModelSelector />
            </div>

            {/* Action Send Button */}
            <button 
              onClick={handleSubmit}
              disabled={!canSend}
              className={`p-2 rounded-xl transition-all duration-200 cursor-pointer flex items-center justify-center shrink-0 shadow-sm ${
                canSend 
                  ? 'bg-brass hover:bg-brass/90 text-background font-bold active:scale-95 shadow-brass/20' 
                  : 'bg-muted/50 text-muted-foreground/40 cursor-not-allowed'
              }`}
              title="Send Message (Enter)"
            >
              <FiArrowUp className="text-base stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
};