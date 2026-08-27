import React, { useState, useMemo } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { 
  FaFilePdf, 
  FaFileWord, 
  FaTrash, 
  FaTimes, 
  FaFileAlt, 
  FaSearch 
} from 'react-icons/fa';

interface HistoryItem {
  id: string;
  name: string;
  type: string;
  size?: string | number;
  uploadedAt?: string;
}

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

  const [searchQuery, setSearchQuery] = useState('');

  // Format file size helper (e.g. 1548576 -> "1.5 MB")
  const formatFileSize = (size?: string | number) => {
    if (!size) return '1.2 MB'; // fallback mock size if missing
    if (typeof size === 'string' && isNaN(Number(size))) return size;
    const bytes = Number(size);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date helper (e.g. ISO string / timestamp -> "Aug 27")
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Today';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  // Filter history based on search query
  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return uploadedHistory;
    return uploadedHistory.filter((item: HistoryItem) => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase().trim())
    );
  }, [uploadedHistory, searchQuery]);

  const renderFileIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'pdf':
        return <FaFilePdf className="text-red-500 text-xl group-hover:scale-110 transition-transform" />;
      case 'docx':
      case 'doc':
      case 'word':
        return <FaFileWord className="text-blue-400 text-xl group-hover:scale-110 transition-transform" />;
      default:
        return <FaFileAlt className="text-brass text-xl group-hover:scale-110 transition-transform" />;
    }
  };

  return (
    <aside 
      className={`h-full flex flex-col bg-card/95 backdrop-blur-md z-20 select-none shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${
        !isMaximized
          ? 'w-0 opacity-0 border-l-0 pointer-events-none'
          : (isHistoryOpen 
              ? 'w-[280px] opacity-100 translate-x-0 border-l border-border/40 shadow-xl' 
              : 'w-0 opacity-0 translate-x-full pointer-events-none border-l-transparent')
      }`}
    >
      {/* ── Header ───────────────────────────────────────── */}
      <div className="w-[280px] h-14 px-4 border-b border-border/30 flex justify-between items-center bg-muted/20 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold uppercase tracking-[0.15em] text-foreground">
            Documents
          </span>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-brass/15 text-brass font-semibold">
            {uploadedHistory.length}
          </span>
        </div>
        <button 
          onClick={toggleHistory}
          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/80 rounded-lg transition-colors cursor-pointer"
          title="Close documents pane"
        >
          <FaTimes className="text-xs" />
        </button>
      </div>

      {/* ── Search Bar ───────────────────────────────────── */}
      <div className="w-[280px] px-3.5 pt-3 pb-1 shrink-0">
        <div className="relative w-full">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 text-[10px]" />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="w-full bg-muted/40 border border-border/40 rounded-xl pl-8 pr-7 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-brass/50 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 hover:text-foreground text-[10px] p-0.5 rounded cursor-pointer"
            >
              <FaTimes />
            </button>
          )}
        </div>
      </div>

      {/* ── 2-Column Grid Documents Area ──────────────────── */}
      <div className="w-[280px] flex-1 overflow-y-auto p-3.5 scrollbar-thin scrollbar-thumb-border/40 scrollbar-track-transparent">
        {filteredHistory.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center gap-2 text-center text-muted-foreground/50 border border-dashed border-border/40 rounded-xl bg-muted/10 p-4">
            <FaFileAlt className="text-2xl opacity-40" />
            <span className="text-[10px] font-mono">
              {searchQuery ? 'No documents match search' : 'No document history'}
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2.5">
            {filteredHistory.map((item: HistoryItem) => {
              const isActive = uploadedFileName === item.name;
              return (
                <div 
                  key={item.id}
                  onClick={() => loadHistoryItem(item as any)}
                  className={`group relative flex flex-col rounded-xl border p-2.5 transition-all duration-200 cursor-pointer overflow-hidden ${
                    isActive 
                      ? 'border-brass/60 bg-brass/10 shadow-[0_0_12px_rgba(212,175,55,0.12)] ring-1 ring-brass/40' 
                      : 'border-border/50 bg-muted/30 hover:bg-muted/70 hover:border-border/80'
                  }`}
                >
                  {/* Delete Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryItem(item.id);
                    }}
                    className="absolute top-1.5 right-1.5 p-1 rounded-md text-muted-foreground/60 hover:text-red-400 hover:bg-red-500/15 transition-all opacity-0 group-hover:opacity-100 z-10 cursor-pointer"
                    title="Delete document"
                  >
                    <FaTrash className="text-[9px]" />
                  </button>

                  {/* Thumbnail Preview Box */}
                  <div className="w-full aspect-[4/3] rounded-lg bg-background/60 border border-border/30 flex flex-col items-center justify-center gap-1 relative overflow-hidden mb-2">
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background/40 pointer-events-none" />
                    {renderFileIcon(item.type)}
                    
                    {/* Size & Extension Pill Tag */}
                    <div className="absolute bottom-1.5 inset-x-1.5 flex justify-between items-center text-[8px] font-mono text-muted-foreground/80 px-1 py-0.5 rounded bg-black/40 backdrop-blur-xs">
                      <span className="uppercase font-bold text-brass">{item.type || 'DOC'}</span>
                      <span>{formatFileSize(item.size)}</span>
                    </div>
                  </div>

                  {/* Document Title & Upload Metadata */}
                  <div className="flex flex-col min-w-0">
                    <span 
                      className={`text-[11px] font-medium leading-tight truncate ${
                        isActive ? 'text-brass font-bold' : 'text-foreground/90 group-hover:text-foreground'
                      }`}
                      title={item.name}
                    >
                      {item.name}
                    </span>
                    
                    <div className="flex items-center justify-between text-[8.5px] font-mono text-muted-foreground mt-1.5">
                      <span className="truncate">{formatDate(item.uploadedAt)}</span>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-brass animate-pulse shrink-0" />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
};