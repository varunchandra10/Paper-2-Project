import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { FaFilePdf, FaFileWord, FaTrash, FaRegFolderOpen } from 'react-icons/fa6';
import { IoClose } from 'react-icons/io5';

export const DocumentsDrawer: React.FC = () => {
  const { 
    uploadedHistory, 
    isHistoryOpen, 
    toggleHistory, 
    loadHistoryItem, 
    deleteHistoryItem 
  } = usePanelStore();

  return (
    <aside 
      className={`absolute left-0 right-0 bottom-0 h-[300px] bg-background/80 border-t border-border/50 shadow-[0_-10px_40px_rgba(0,0,0,0.1)] backdrop-blur-xl flex flex-col z-10 transform transition-all duration-400 cubic-bezier(0.4, 0, 0.2, 1) rounded-t-2xl ${
        isHistoryOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="Uploaded Documents History"
    >
      {/* Header bar inside history drawer */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-border/40">
        <div className="flex items-center gap-2">
          <FaRegFolderOpen className="text-foreground/60 text-lg" />
          <span className="font-serif text-sm font-semibold text-foreground/90 tracking-wide">
            Document History
          </span>
        </div>
        <button 
          onClick={toggleHistory}
          className="p-1.5 rounded-full text-foreground/50 hover:text-foreground hover:bg-foreground/10 transition-colors focus:outline-none focus:ring-2 focus:ring-brass/50"
          aria-label="Close History Panel"
        >
          <IoClose className="text-lg" />
        </button>
      </div>

      {/* List of files */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-gradient-to-b from-transparent to-black/5 scrollbar-thin scrollbar-thumb-foreground/10 scrollbar-track-transparent">
        {uploadedHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-foreground/40 py-8 border-2 border-dashed border-border/30 rounded-xl mx-2">
            <FaRegFolderOpen className="text-3xl opacity-50" />
            <span className="text-xs font-medium">No documents uploaded yet.</span>
            <span className="text-[10px] opacity-70">Drop a file to populate.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5 px-2">
            {uploadedHistory.map((item) => (
              <div 
                key={item.id} 
                className="group flex items-center justify-between p-3 rounded-xl border border-border/30 bg-background/50 hover:bg-background/90 hover:border-brass/40 hover:shadow-sm transition-all duration-300"
              >
                <div 
                  onClick={() => loadHistoryItem(item)}
                  className="flex-1 flex items-center gap-4 cursor-pointer select-none overflow-hidden"
                >
                  <div className="p-2.5 rounded-lg bg-foreground/5 group-hover:bg-background transition-colors">
                    {item.type === 'pdf' ? (
                      <FaFilePdf className="text-brass/90 text-lg" />
                    ) : (
                      <FaFileWord className="text-blue-500/90 text-lg" />
                    )}
                  </div>
                  
                  <div className="flex flex-col text-left min-w-0">
                    <span className="text-xs font-medium font-sans text-foreground/90 truncate max-w-[220px] group-hover:text-brass transition-colors">
                      {item.name}
                    </span>
                    <span className="text-[10px] text-muted-foreground mt-0.5 select-none flex items-center gap-1.5">
                      <span>{item.timestamp}</span>
                      <span className="w-1 h-1 rounded-full bg-border"></span>
                      <span className={`font-semibold ${item.decompScore > 70 ? 'text-green-500/80' : 'text-brass/80'}`}>
                        Score: {item.decompScore}%
                      </span>
                    </span>
                  </div>
                </div>
                
                <button
                  onClick={() => deleteHistoryItem(item.id)}
                  className="text-foreground/30 hover:text-red-500 p-2 rounded-lg hover:bg-red-500/10 transition-all select-none opacity-0 group-hover:opacity-100 focus:opacity-100"
                  title="Remove from history"
                >
                  <FaTrash className="text-sm" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};
