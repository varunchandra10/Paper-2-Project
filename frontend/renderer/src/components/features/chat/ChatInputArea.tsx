import React, { useRef, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { ModelSelector } from '../../ui/ModelSelector';
import {
  IconPlus, IconFileText, IconTerminal,
  IconClose, IconFile, IconArrowUp,
  IconCheckCircle, IconAlertCircle, IconLoader
} from '../../ui/Icons';

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
    <div className="w-full max-w-[800px] px-4 pt-2 pb-1 z-20 shrink-0">
      <div className="flex flex-col gap-2">
        
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
              <IconFileText className="text-xs transition-transform group-hover:scale-110" />
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
              <IconTerminal className="text-xs transition-transform group-hover:scale-110" />
            </button>
          </div>
        )}

        {/* Status Loader */}
        {isAnalyzing && (
          <div className="flex items-center gap-2 px-2 py-1 select-none text-[10px] font-mono text-brass font-semibold tracking-wide bg-brass/5 border border-brass/20 rounded-lg w-fit animate-pulse">
            <IconLoader className="w-3 h-3 animate-spin text-brass shrink-0" />
            <span>Processing document pipeline...</span>
          </div>
        )}

        {/* Floating Input Card Container */}
        <div className="relative border app-border rounded-2xl bg-[var(--bg-card)] backdrop-blur-xl shadow-[0_10px_35px_rgba(0,0,0,0.08)] focus-within:border-[var(--accent-border)] focus-within:shadow-[0_0_24px_var(--accent-subtle)] transition-all duration-300 flex flex-col">
          
          {/* Staged File Pill Badge */}
          {stagedFile && (
            <div className="px-3.5 pt-3 pb-1 select-none flex items-center gap-2 flex-wrap border-b app-border bg-[var(--bg-base)]/50 rounded-t-2xl overflow-hidden">
              <div className="relative inline-flex items-center gap-2 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] text-[11px] font-mono font-semibold px-3 py-1.5 max-w-full overflow-hidden shadow-xs">
                <IconFile className="shrink-0 text-xs" />
                <span className="truncate max-w-[240px]" title={stagedFile.filename}>
                  {stagedFile.filename}
                </span>

                {!isAnalyzing && onClearStagedFile && (
                  <button
                    onClick={onClearStagedFile}
                    className="ml-1 p-0.5 rounded-full hover:bg-[var(--accent-subtle)] text-[var(--accent)] transition-colors shrink-0 cursor-pointer"
                    title="Remove file"
                  >
                    <IconClose className="text-xs" />
                  </button>
                )}

                {/* Progress bar overlay during active analysis */}
                {isAnalyzing && (
                  <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--accent-subtle)]">
                    <div 
                      className="h-full bg-[var(--accent)] transition-all duration-500 ease-out"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Status Badges */}
              {analysisStatus === 'success' && (
                <div className="inline-flex items-center gap-1.5 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold font-mono tracking-wider uppercase px-2.5 py-1 rounded-xl select-none shadow-xs shrink-0">
                  <IconCheckCircle className="text-xs" />
                  <span>Verified</span>
                </div>
              )}
              {analysisStatus === 'error' && (
                <div className="inline-flex items-center gap-1.5 bg-red-500/15 border border-red-500/30 text-red-400 text-[10px] font-bold font-mono tracking-wider uppercase px-2.5 py-1 rounded-xl select-none shadow-xs shrink-0">
                  <IconAlertCircle className="text-xs" />
                  <span>Ingestion Failed</span>
                </div>
              )}
            </div>
          )}

          {/* Dynamic Auto-Resizing Textarea */}
          <div className="px-3 pt-2 pb-0.5">
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
              className="w-full bg-transparent outline-none resize-none text-[13px] text-[var(--text-main)] placeholder-[var(--text-muted)] font-sans leading-relaxed min-h-[28px] max-h-[160px] disabled:opacity-50"
            />
          </div>

          {/* Bottom Bar: Model Selector & Actions */}
          <div className="px-2.5 pb-1.5 pt-0.5 flex justify-between items-center select-none relative z-30">
            <div className="flex items-center gap-1.5">
              <button 
                onClick={handleBrowseFile}
                disabled={isAnalyzing}
                className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] rounded-lg transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed active:scale-95 border border-transparent"
                title="Upload PDF/Document"
              >
                <IconPlus className="text-sm" />
              </button>

              <div className="h-3.5 w-[1px] bg-[var(--border-color)] mx-0.5" />

              <ModelSelector />
            </div>

            {/* Action Send Button */}
            <button 
              onClick={handleSubmit}
              disabled={!canSend}
              className={`w-7 h-7 rounded-lg transition-all duration-200 cursor-pointer flex items-center justify-center shrink-0 shadow-xs ${
                canSend 
                  ? 'bg-[var(--accent)] hover:opacity-90 text-white font-bold active:scale-95' 
                  : 'bg-[var(--bg-base)] text-[var(--text-muted)] opacity-40 cursor-not-allowed border app-border'
              }`}
              title="Send Message"
            >
              <IconArrowUp className="text-xs" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};