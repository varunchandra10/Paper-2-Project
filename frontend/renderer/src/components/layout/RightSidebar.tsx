import React, { useState, useMemo, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import {
  IconPdf, IconWord, IconDoc, IconTrash,
  IconClose, IconSearch, IconColor
} from '../ui/Icons';

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
    deleteHistoryItem,
    fetchUploadedPapers 
  } = usePanelStore();

  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchUploadedPapers();
  }, [fetchUploadedPapers]);

  // Format file size helper (e.g. 1548576 -> "1.5 MB")
  const formatFileSize = (size?: string | number) => {
    if (!size) return '1.2 MB';
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
        return <IconPdf className={`${IconColor.accent} text-xl group-hover:scale-110 transition-transform duration-200`} />;
      case 'docx':
      case 'doc':
      case 'word':
        return <IconWord className={`${IconColor.accent} text-xl group-hover:scale-110 transition-transform duration-200`} />;
      default:
        return <IconDoc className={`${IconColor.muted} text-xl group-hover:scale-110 transition-transform duration-200`} />;
    }
  };

  return (
    <aside 
      className={`h-full flex flex-col bg-card/95 backdrop-blur-xl z-20 select-none shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${
        !isMaximized
          ? 'w-0 opacity-0 border-l-0 pointer-events-none'
          : (isHistoryOpen 
              ? 'w-[280px] opacity-100 translate-x-0 border-l border-border/60 shadow-xl' 
              : 'w-0 opacity-0 translate-x-full pointer-events-none border-l-transparent')
      }`}
    >
      {/* ── Header Bar ───────────────────────────────────────── */}
      <div className="w-[280px] h-14 px-4 border-b border-border/50 flex justify-between items-center bg-card shrink-0">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-[11px] font-bold uppercase tracking-widest text-foreground">
            Research Library
          </span>
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-brass/15 text-brass border border-brass/30">
            {uploadedHistory.length}
          </span>
        </div>
        <button 
          onClick={toggleHistory}
          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/60 rounded-xl transition-colors cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-brass"
          title="Close documents pane"
          aria-label="Close documents pane"
        >
          <IconClose className="text-xs" />
        </button>
      </div>

      {/* ── Document Search Filter ───────────────────────────────────── */}
      <div className="w-[280px] px-3.5 pt-3 pb-1 shrink-0 font-mono">
        <div className="relative w-full">
          <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-[10px]" />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers & docs..."
            className="w-full bg-input border border-border/60 rounded-xl pl-8 pr-7 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-brass focus:ring-1 focus:ring-brass transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-[10px] p-1 rounded-md cursor-pointer"
            >
              <IconClose />
            </button>
          )}
        </div>
      </div>

      {/* ── 2-Column Grid Documents Area ──────────────────── */}
      <div className="w-[280px] flex-1 overflow-y-auto p-3.5 scrollbar-thin scrollbar-thumb-border/40 scrollbar-track-transparent">
        {filteredHistory.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center gap-2 text-center text-muted-foreground border border-dashed border-border/40 rounded-2xl bg-muted/20 p-4 font-mono">
            <IconDoc className="text-2xl text-muted-foreground/50" />
            <span className="text-[10px]">
              {searchQuery ? 'No documents match search' : 'No research papers uploaded'}
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
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      loadHistoryItem(item as any);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  className={`group relative flex flex-col rounded-2xl border p-2.5 transition-all duration-200 cursor-pointer overflow-hidden outline-none focus-visible:ring-2 focus-visible:ring-brass ${
                    isActive 
                      ? 'border-brass bg-brass/15 shadow-[0_0_14px_rgba(212,163,56,0.2)]' 
                      : 'border-border/60 bg-card/60 hover:bg-muted/60 hover:border-brass/40'
                  }`}
                >
                  {/* HUD Corner Bracket Accents for Active Items */}
                  {isActive && (
                    <>
                      <div className="absolute top-1 left-1 w-1.5 h-1.5 border-t border-l border-brass pointer-events-none" />
                      <div className="absolute top-1 right-1 w-1.5 h-1.5 border-t border-r border-brass pointer-events-none" />
                    </>
                  )}

                  {/* Delete Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryItem(item.id);
                    }}
                    className="absolute top-1.5 right-1.5 p-1 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/15 transition-all opacity-0 group-hover:opacity-100 z-10 cursor-pointer outline-none"
                    title="Delete document"
                  >
                    <IconTrash className="text-[9px]" />
                  </button>

                  {/* Thumbnail Preview Card */}
                  <div className="w-full aspect-[4/3] rounded-xl bg-background/80 border border-border/50 flex flex-col items-center justify-center gap-1 relative overflow-hidden mb-2">
                    {renderFileIcon(item.type)}
                    
                    {/* Size & Type Badge */}
                    <div className="absolute bottom-1.5 inset-x-1.5 flex justify-between items-center text-[8px] font-mono text-muted-foreground px-1 py-0.5 rounded bg-muted/80 backdrop-blur-xs border border-border/40">
                      <span className="uppercase font-bold text-brass">{item.type || 'PDF'}</span>
                      <span>{formatFileSize(item.size)}</span>
                    </div>
                  </div>

                  {/* Document Title & Upload Metadata */}
                  <div className="flex flex-col min-w-0 font-mono">
                    <span 
                      className={`text-[11px] font-bold leading-tight truncate ${
                        isActive ? 'text-brass' : 'text-foreground/90 group-hover:text-foreground'
                      }`}
                      title={item.name}
                    >
                      {item.name}
                    </span>
                    
                    <div className="flex items-center justify-between text-[8.5px] text-muted-foreground mt-1">
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