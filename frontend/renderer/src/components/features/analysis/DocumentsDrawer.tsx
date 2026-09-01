import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { IconPdf, IconWord, IconTrash, IconFolderOpen, IconClose, IconColor } from '../../ui/Icons';

export const DocumentsDrawer: React.FC = () => {
  const { 
    uploadedHistory, 
    isHistoryOpen, 
    toggleHistory, 
    loadHistoryItem, 
    deleteHistoryItem,
    fetchUploadedPapers 
  } = usePanelStore();

  React.useEffect(() => {
    fetchUploadedPapers();
  }, [fetchUploadedPapers]);

  return (
    <aside 
      className={`absolute left-0 right-0 bottom-0 h-[300px] bg-[var(--bg-card)] border-t app-border shadow-[0_-10px_40px_rgba(0,0,0,0.15)] backdrop-blur-xl flex flex-col z-30 transform transition-all duration-400 cubic-bezier(0.4, 0, 0.2, 1) rounded-t-2xl text-[var(--text-main)] ${
        isHistoryOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="Uploaded Documents History"
    >
      {/* Header bar inside history drawer */}
      <div className="flex justify-between items-center px-6 py-4 border-b app-border">
        <div className="flex items-center gap-2">
          <IconFolderOpen className="text-[var(--accent)] text-lg" />
          <span className="font-sans text-sm font-bold text-[var(--text-main)] tracking-wide">
            Document History
          </span>
        </div>
        <button 
          onClick={toggleHistory}
          className="p-1.5 rounded-full text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 cursor-pointer"
          aria-label="Close History Panel"
        >
          <IconClose className="text-lg" />
        </button>
      </div>

      {/* List of files */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent">
        {uploadedHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-[var(--text-muted)] py-8 border-2 border-dashed app-border rounded-xl mx-2 bg-[var(--bg-base)]">
            <IconFolderOpen className="text-3xl opacity-50 text-[var(--text-muted)]" />
            <span className="text-xs font-medium">No documents uploaded yet.</span>
            <span className="text-[10px] opacity-70">Drop a file to populate.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5 px-2">
            {uploadedHistory.map((item) => (
              <div 
                key={item.id} 
                className="group flex items-center justify-between p-3 rounded-xl border app-border bg-[var(--bg-base)] hover:bg-[var(--accent-subtle)] hover:border-[var(--accent-border)] hover:shadow-sm transition-all duration-200"
              >
                <div 
                  onClick={() => loadHistoryItem(item)}
                  className="flex-1 flex items-center gap-4 cursor-pointer select-none overflow-hidden"
                >
                  <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border app-border group-hover:border-[var(--accent-border)] transition-colors">
                    {item.type === 'pdf' ? (
                      <IconPdf className={`${IconColor.accent} text-lg`} />
                    ) : (
                      <IconWord className={`${IconColor.accent} text-lg`} />
                    )}
                  </div>
                  
                  <div className="flex flex-col text-left min-w-0 font-sans">
                    <span className="text-xs font-semibold text-[var(--text-main)] truncate max-w-[220px] group-hover:text-[var(--accent)] transition-colors">
                      {item.name}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] mt-0.5 select-none flex items-center gap-1.5 font-mono">
                      <span>{item.timestamp}</span>
                      <span className="w-1 h-1 rounded-full bg-[var(--text-muted)] opacity-40"></span>
                      <span className={`font-semibold ${item.decompScore > 70 ? 'text-emerald-400' : 'text-[var(--accent)]'}`}>
                        Score: {item.decompScore}%
                      </span>
                    </span>
                  </div>
                </div>
                
                <button
                  onClick={() => deleteHistoryItem(item.id)}
                  className="text-[var(--text-muted)] hover:text-red-400 p-2 rounded-lg hover:bg-red-500/10 transition-all select-none opacity-0 group-hover:opacity-100 focus:opacity-100 cursor-pointer"
                  title="Remove from history"
                >
                  <IconTrash className="text-sm" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};
