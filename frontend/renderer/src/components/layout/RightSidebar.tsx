import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaFilePdf, FaFileWord, FaTrash, FaTimes } from 'react-icons/fa';

interface RightSidebarProps {
  isMaximized: boolean;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ isMaximized }) => {
  const { 
    isHistoryOpen, 
    toggleHistory, 
    uploadedHistory, 
    uploadedFileName, 
    loadHistoryItem, 
    deleteHistoryItem 
  } = usePanelStore();

  if (!isMaximized) return null;

  return (
    <aside 
      className={`h-full flex flex-col bg-card border-l border-border/55 z-20 select-none shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${
        isHistoryOpen 
          ? 'w-[260px] opacity-100 translate-x-0' 
          : 'w-0 opacity-0 translate-x-full pointer-events-none border-l-transparent'
      }`}
    >
      {/* Header with Title and Close Trigger */}
      <div className="w-[260px] p-4 border-b border-border/40 flex justify-between items-center bg-background/5 shrink-0">
        <span className="text-[10px] font-mono font-bold uppercase tracking-[0.15em] text-foreground/80">
          Documents History
        </span>
        <button 
          onClick={toggleHistory}
          className="p-1 text-foreground/45 hover:text-foreground hover:bg-foreground/5 rounded transition-all cursor-pointer"
          title="Collapse history pane"
        >
          <FaTimes className="text-[10px]" />
        </button>
      </div>

      {/* History List */}
      <div className="w-[260px] flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-2.5 scrollbar-thin scrollbar-thumb-border/20 scrollbar-track-transparent">
        {uploadedHistory.length === 0 ? (
          <div className="px-3 py-6 text-center text-[10px] font-mono text-foreground/45 border border-dashed border-border/20 rounded-lg">
            No past records
          </div>
        ) : (
          uploadedHistory.map((item) => (
            <div 
              key={item.id}
              className={`group flex items-center justify-between p-2.5 rounded-lg border transition-all duration-300 cursor-pointer ${
                uploadedFileName === item.name 
                  ? 'border-brass/30 bg-brass/5' 
                  : 'border-transparent hover:bg-foreground/5'
              }`}
              onClick={() => loadHistoryItem(item)}
            >
              <div className="flex items-center gap-2.5 truncate flex-1 animate-fade-in">
                {item.type === 'pdf' ? (
                  <FaFilePdf className="text-red-500 shrink-0 text-sm" />
                ) : (
                  <FaFileWord className="text-blue-400 shrink-0 text-sm" />
                )}
                <span className="text-xs truncate font-medium text-foreground/80 group-hover:text-foreground">
                  {item.name}
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteHistoryItem(item.id);
                }}
                className="p-1 text-foreground/30 hover:text-red-500 hover:bg-red-500/10 rounded transition-all shrink-0 opacity-0 group-hover:opacity-100"
                title="Delete record"
              >
                <FaTrash className="text-[10px]" />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
};
