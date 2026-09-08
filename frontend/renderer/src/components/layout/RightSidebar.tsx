import React, { useState, useMemo, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import {
  IconPdf, IconWord, IconDoc, IconTrash,
  IconClose, IconSearch, IconColor
} from '../ui/Icons';
import { formatFileSize, formatDate } from '../../utils/formatters';

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
      className={`h-full flex flex-col bg-[var(--bg-sidebar)] backdrop-blur-xl z-20 select-none shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${
        !isMaximized
          ? 'w-0 opacity-0 border-l-0 pointer-events-none'
          : (isHistoryOpen 
              ? 'w-[280px] opacity-100 translate-x-0 border-l border-[var(--border-color)] shadow-xl' 
              : 'w-0 opacity-0 translate-x-full pointer-events-none border-l-transparent')
      }`}
    >
      {/* ── Header Bar ───────────────────────────────────────── */}
      <div className="w-[280px] h-14 px-4 border-b border-[var(--border-color)] flex justify-between items-center bg-[var(--bg-sidebar)] shrink-0">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-[11px] font-bold uppercase tracking-widest text-[var(--text-main)]">
            Research Library
          </span>
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]">
            {uploadedHistory.length}
          </span>
        </div>
        <button 
          onClick={toggleHistory}
          className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] rounded-xl transition-colors cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
          title="Close documents pane"
          aria-label="Close documents pane"
        >
          <IconClose className="text-xs" />
        </button>
      </div>

      {/* ── Document Search Filter ───────────────────────────────────── */}
      <div className="w-[280px] px-3.5 pt-3 pb-1 shrink-0 font-mono">
        <div className="relative w-full">
          <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-[10px]" />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers & docs..."
            className="w-full bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl pl-8 pr-7 py-2 text-xs text-[var(--text-main)] placeholder:text-[var(--text-muted)] outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-main)] text-[10px] p-1 rounded-md cursor-pointer"
            >
              <IconClose />
            </button>
          )}
        </div>
      </div>

      {/* ── 2-Column Grid Documents Area ──────────────────── */}
      <div className="w-[280px] max-w-full flex-1 overflow-y-auto overflow-x-hidden p-3.5 scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent">
        {filteredHistory.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center gap-2 text-center text-[var(--text-muted)] border border-dashed border-[var(--border-color)] rounded-2xl bg-[var(--bg-card)]/40 p-4 font-mono">
            <IconDoc className="text-2xl text-[var(--text-muted)]/50" />
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
                  className={`group relative flex flex-col rounded-2xl border p-2.5 transition-all duration-200 cursor-pointer overflow-hidden outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] ${
                    isActive 
                      ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-[0_0_14px_rgba(218,119,86,0.2)]' 
                      : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)]/30 hover:border-[var(--accent-border)]'
                  }`}
                >
                  {/* HUD Corner Bracket Accents for Active Items */}
                  {isActive && (
                    <>
                      <div className="absolute top-1 left-1 w-1.5 h-1.5 border-t border-l border-[var(--accent)] pointer-events-none" />
                      <div className="absolute top-1 right-1 w-1.5 h-1.5 border-t border-r border-[var(--accent)] pointer-events-none" />
                    </>
                  )}

                  {/* Delete Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryItem(item.id);
                    }}
                    className="absolute top-1.5 right-1.5 p-1 rounded-lg text-[var(--text-muted)] hover:text-destructive hover:bg-destructive/15 transition-all opacity-0 group-hover:opacity-100 z-10 cursor-pointer outline-none"
                    title="Delete document"
                  >
                    <IconTrash className="text-[9px]" />
                  </button>

                  {/* Thumbnail Preview Card */}
                  <div className="w-full aspect-[4/3] rounded-xl bg-[var(--bg-base)] border border-[var(--border-color)] flex flex-col items-center justify-center gap-1 relative overflow-hidden mb-2">
                    {renderFileIcon(item.type)}
                    
                    {/* Size & Type Badge */}
                    <div className="absolute bottom-1.5 inset-x-1.5 flex justify-between items-center text-[8px] font-mono text-[var(--text-muted)] px-1 py-0.5 rounded bg-[var(--bg-card)]/80 backdrop-blur-xs border border-[var(--border-color)]">
                      <span className="uppercase font-bold text-[var(--accent)]">{item.type || 'PDF'}</span>
                      <span>{formatFileSize(item.size)}</span>
                    </div>
                  </div>

                  {/* Document Title & Upload Metadata */}
                  <div className="flex flex-col min-w-0 font-mono">
                    <span 
                      className={`text-[11px] font-bold leading-tight truncate ${
                        isActive ? 'text-[var(--accent)]' : 'text-[var(--text-main)]/90 group-hover:text-[var(--text-main)]'
                      }`}
                      title={item.name}
                    >
                      {item.name}
                    </span>
                    
                    <div className="flex items-center justify-between text-[8.5px] text-[var(--text-muted)] mt-1">
                      <span className="truncate">{formatDate(item.uploadedAt)}</span>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse shrink-0" />
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