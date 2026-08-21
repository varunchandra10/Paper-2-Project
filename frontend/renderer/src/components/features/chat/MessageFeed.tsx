import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { ReportView } from '../analysis/ReportView';
import { DropZone } from '../../ui/DropZone';
import { FiFileText, FiPlus } from 'react-icons/fi';

interface MessageFeedProps {
  isMaximized: boolean;
}

export const MessageFeed: React.FC<MessageFeedProps> = ({ isMaximized }) => {
  const { uploadedFileName, isAnalyzing, reportContent } = usePanelStore();

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-6 scrollbar-thin scrollbar-thumb-border/20 scrollbar-track-transparent z-10 relative">
      
      {/* Welcome message when idle */}
      {!uploadedFileName && (
        <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 max-w-[500px] mx-auto mt-6 select-none">
          <div className="w-12 h-12 rounded-xl bg-brass/5 border border-brass/25 flex items-center justify-center shadow-lg shadow-brass/5">
            <FiFileText className="text-brass text-2xl animate-pulse" />
          </div>
          <h2 className="text-lg font-black tracking-tight text-foreground/90">
            Welcome to Paper_2_Project
          </h2>
          <p className="text-[11px] text-foreground/75 font-mono tracking-wide leading-relaxed mb-2">
            To begin, click the file button {!isMaximized && <FiFileText className="inline text-xs mx-0.5" />} {isMaximized ? "plus" : ""} button <FiPlus className="inline text-xs mx-0.5" /> in the chatbox below{isMaximized ? ", or drop files directly below." : "."}
          </p>

          {/* Integrated file drag-and-drop picker zones */}
          {isMaximized && (
            <div className="w-full border border-border/40 rounded-2xl p-3 bg-card/30">
              <DropZone />
            </div>
          )}
        </div>
      )}

      {/* User prompt message once file is selected */}
      {uploadedFileName && (
        <div className="flex flex-col gap-1.5 items-end self-end max-w-[85%] font-sans select-none">
          <div className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest px-2">User</div>
          <div className="bg-brass/10 border border-brass/20 text-foreground px-4 py-3 rounded-2xl rounded-tr-sm shadow-md text-xs leading-relaxed">
            Analyze and adapt model paper: <strong className="font-semibold text-brass">{uploadedFileName}</strong>
          </div>
        </div>
      )}

      {/* System analysis response */}
      {uploadedFileName && (
        <div className="flex flex-col gap-1.5 items-start self-start max-w-[90%] font-sans">
          <div className="text-[9px] font-mono text-brass uppercase tracking-widest px-2 flex items-center gap-1.5 select-none">
            <span className="w-1.5 h-1.5 bg-brass rounded-full animate-ping" />
            Assistant
          </div>
          <div className="bg-black/30 border border-border/50 text-foreground/90 px-5 py-4 rounded-2xl rounded-tl-sm shadow-md text-xs leading-relaxed w-full">
            {isAnalyzing && !reportContent ? (
              <div className="flex flex-col gap-2 font-mono text-[10px] text-foreground/60 select-none">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-brass rounded-full animate-bounce" />
                  <span>Processing paper sections...</span>
                </div>
                <span className="text-[9px] text-muted-foreground opacity-50 tracking-wider">Please review logs for pipeline progress details.</span>
              </div>
            ) : (
              <ReportView />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
