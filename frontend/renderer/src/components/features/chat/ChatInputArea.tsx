import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { ModelSelector } from '../../ui/ModelSelector';
import { FiPlus, FiSend, FiFileText, FiTerminal } from 'react-icons/fi';

interface ChatInputAreaProps {
  isMaximized: boolean;
  chatInputValue: string;
  setChatInputValue: (val: string) => void;
  handleBrowseFile: () => void;
}

export const ChatInputArea: React.FC<ChatInputAreaProps> = ({
  isMaximized,
  chatInputValue,
  setChatInputValue,
  handleBrowseFile,
}) => {
  const { 
    isHistoryOpen, 
    toggleHistory,
    isLogsOpen,
    toggleLogs
  } = usePanelStore();

  return (
    <footer className="p-4 z-20 shrink-0 bg-background bg-gradient-to-t from-background via-background to-transparent pt-5">
      <div className="max-w-[800px] mx-auto flex flex-col gap-2.5">
        
        {/* Header Toolbar (Docs & Terminal icon-only buttons, separated above the chat card container) */}
        {!isMaximized && (
          <div className="flex gap-2.5 px-1 select-none">
            {/* Docs Drawer Toggle */}
            <button 
              onClick={toggleHistory}
              className={`p-2 rounded-lg border transition-all duration-300 cursor-pointer flex items-center justify-center w-8 h-8 ${
                isHistoryOpen 
                  ? 'border-red-500/50 bg-red-500/10 text-red-500 shadow-[0_0_12px_rgba(239,68,68,0.15)]' 
                  : 'border-foreground/30 text-foreground/50 hover:bg-foreground/5 hover:text-foreground'
              }`}
              title="Documents & History"
            >
              <FiFileText className="text-sm" />
            </button>

            {/* Terminal Drawer Toggle */}
            <button 
              onClick={toggleLogs}
              className={`p-2 rounded-lg border transition-all duration-300 cursor-pointer flex items-center justify-center w-8 h-8 ${
                isLogsOpen 
                  ? 'border-amber-500/50 bg-amber-500/10 text-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.15)]' 
                  : 'border-foreground/30 text-foreground/50 hover:bg-foreground/5 hover:text-foreground'
              }`}
              title="Terminal Console"
            >
              <FiTerminal className="text-sm" />
            </button>
          </div>
        )}

        {/* Chat input box */}
        <div className="flex flex-col bg-card rounded-2xl shadow-lg relative overflow-visible transition-colors duration-300">

        {/* Textarea Input */}
        <div className="px-4 pt-2.5">
          <textarea 
            rows={2}
            value={chatInputValue}
            onChange={(e) => setChatInputValue(e.target.value)}
            placeholder="Ask anything, @ to mention, / for actions"
            className="w-full bg-transparent outline-none resize-none text-xs placeholder-foreground/30 text-foreground/90 font-sans leading-relaxed"
          />
        </div>

        {/* Bottom Bar: Model Selector, Plus, Send */}
        <div className="px-4 pb-3 pt-2.5 flex justify-between items-center z-10 select-none">
          <div className="flex items-center gap-3">
            {/* Plus Button */}
            <button 
              onClick={handleBrowseFile}
              className="p-1.5 text-foreground/40 hover:text-foreground hover:bg-foreground/5 rounded-lg transition-all cursor-pointer"
              title="Upload PDF Paper"
            >
              <FiPlus className="text-sm" />
            </button>

            {/* Models dropdown menu */}
            <ModelSelector />
          </div>

          {/* Send Button */}
          <button 
            className="p-2 bg-brass/10 hover:bg-brass/25 border border-brass/25 hover:border-brass text-brass rounded-lg transition-all active:scale-95 cursor-pointer shadow-sm hover:shadow-brass/10"
            title="Send Message"
          >
            <FiSend className="text-xs" />
          </button>
        </div>
      </div>
    </div>
  </footer>
  );
};
