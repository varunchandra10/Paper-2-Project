import React, { useState, useMemo, useEffect, useRef } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { SkinLoader } from '../ui/SkinLoader';
import { API_BASE } from '../../store/utils/storeUtils';
import {
  IconPdf, IconWord, IconDoc, IconTrash,
  IconClose, IconSearch, IconInfo,
  IconCopy, IconCheck, IconDownload,
  IconColor
} from '../ui/Icons';
import { formatFileSize, formatDate } from '../../utils/formatters';

interface HistoryItem {
  id: string;
  name: string;
  type: string;
  size?: string | number;
  uploadedAt?: string;
  timestamp?: string;
  title?: string;
  authors?: string[];
  pageCount?: number;
  rawDate?: string;
}

export const DocumentHistoryList: React.FC<{ isOpen: boolean; onSelect?: () => void }> = ({ isOpen, onSelect }) => {
  const { 
    uploadedHistory, 
    uploadedFileName, 
    loadHistoryItem, 
    deleteHistoryItem,
    deleteMultipleHistoryItems,
    fetchUploadedPapers,
    isPapersLoading
  } = usePanelStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeInfoId, setActiveInfoId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchUploadedPapers();
  }, [fetchUploadedPapers]);

  // Dismiss popover when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setActiveInfoId(null);
      }
    };
    if (activeInfoId) {
      document.addEventListener('click', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('click', handleOutsideClick);
    };
  }, [activeInfoId]);

  // Selection handlers
  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleDownloadSelected = () => {
    if (selectedIds.size === 0) return;
    const selectedItems = uploadedHistory.filter((item: HistoryItem) => selectedIds.has(item.id));
    selectedItems.forEach((item: HistoryItem) => {
      const pid = item.id.startsWith('paper_') ? item.id : `paper_${item.id}`;
      const url = `${API_BASE}/papers/${pid}/pdf`;
      const link = document.createElement('a');
      link.href = url;
      link.download = item.name.endsWith('.pdf') ? item.name : `${item.name}.pdf`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  const handleDeleteSelected = () => {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    if (deleteMultipleHistoryItems) {
      deleteMultipleHistoryItems(ids);
    } else {
      ids.forEach((id) => deleteHistoryItem(id));
    }
    setSelectedIds(new Set());
    setActiveInfoId(null);
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
        return <IconPdf className={`${IconColor.accent} text-lg group-hover:scale-110 transition-transform duration-200`} />;
      case 'docx':
      case 'doc':
      case 'word':
        return <IconWord className={`${IconColor.accent} text-lg group-hover:scale-110 transition-transform duration-200`} />;
      default:
        return <IconDoc className={`${IconColor.muted} text-lg group-hover:scale-110 transition-transform duration-200`} />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden select-none">
      {/* Search Input Filter Area */}
      <div className="px-3 pt-2.5 pb-1.5 shrink-0 font-mono">
        <div className="relative w-full">
          <IconSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-[10px]" />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers & docs..."
            className="w-full bg-[var(--bg-base)] border app-border rounded-lg pl-7 pr-6 py-1 text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-main)] text-[10px] p-0.5 rounded cursor-pointer"
            >
              <IconClose />
            </button>
          )}
        </div>
      </div>

      {/* Static Selection / Action Bar (Blocked until user selects any PDF) */}
      {(() => {
        const hasSelected = selectedIds.size > 0;
        return (
          <div 
            className={`mx-2.5 mb-2 px-3 py-1.5 rounded-xl border flex items-center justify-between text-xs select-none transition-all duration-200 ${
              hasSelected 
                ? 'bg-[var(--bg-card)] border-[var(--accent-border)] shadow-xs' 
                : 'bg-[var(--bg-card)]/40 border-[var(--border-color)] opacity-60'
            }`}
          >
            {/* Selected : __ */}
            <div className="flex items-center gap-1.5 min-w-0">
              <span className={`text-[11px] font-sans font-medium select-none ${hasSelected ? 'text-[var(--text-main)]' : 'text-[var(--text-muted)]'}`}>
                Selected :
              </span>
              <span className={`px-1.5 py-0.2 text-[10px] font-mono font-bold rounded-md border transition-colors select-none ${
                hasSelected 
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent-border)]' 
                  : 'bg-[var(--bg-base)] text-[var(--text-muted)] border-[var(--border-color)]'
              }`}>
                {selectedIds.size}
              </span>
            </div>

            {/* Actions: [Download icon] | [Delete icon] */}
            <div className="flex items-center gap-1.5 shrink-0">
              {/* Download Button */}
              <button
                onClick={handleDownloadSelected}
                disabled={!hasSelected}
                className={`p-1.5 rounded-lg border transition-all flex items-center justify-center ${
                  hasSelected 
                    ? 'bg-[var(--bg-base)] border-[var(--accent-border)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white active:scale-95 cursor-pointer shadow-xs' 
                    : 'bg-[var(--bg-base)]/50 border-[var(--border-color)] text-[var(--text-muted)] opacity-40 cursor-not-allowed pointer-events-none'
                }`}
                data-tooltip={hasSelected ? `Download ${selectedIds.size} selected file(s)` : "Select files to download"}
                data-tooltip-pos="top"
              >
                <IconDownload className="text-xs" />
              </button>

              {/* Vertical Separator Divider */}
              <div className="h-3.5 w-[1px] bg-[var(--border-color)]" />

              {/* Delete Button */}
              <button
                onClick={handleDeleteSelected}
                disabled={!hasSelected}
                className={`p-1.5 rounded-lg border transition-all flex items-center justify-center ${
                  hasSelected 
                    ? 'bg-[var(--bg-base)] border-red-500/40 text-red-400 hover:bg-red-500 hover:text-white active:scale-95 cursor-pointer shadow-xs' 
                    : 'bg-[var(--bg-base)]/50 border-[var(--border-color)] text-[var(--text-muted)] opacity-40 cursor-not-allowed pointer-events-none'
                }`}
                data-tooltip={hasSelected ? `Delete ${selectedIds.size} selected file(s)` : "Select files to delete"}
                data-tooltip-pos="top"
              >
                <IconTrash className="text-xs" />
              </button>
            </div>
          </div>
        );
      })()}

      {/* Document Items Grid List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-2.5 py-1 space-y-1.5 scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent w-full max-w-full">
        {isPapersLoading ? (
          <SkinLoader type="document" />
        ) : filteredHistory.length === 0 ? (
          <div className="py-8 flex flex-col items-center justify-center text-center p-3 rounded-xl border border-dashed app-border bg-[var(--bg-base)] font-sans">
            <IconDoc className="text-[var(--text-muted)] text-xl mb-1.5" />
            <span className="text-[11px] text-[var(--text-muted)]">
              {searchQuery ? 'No documents match search' : 'No research papers uploaded'}
            </span>
          </div>
        ) : (
          filteredHistory.map((item: HistoryItem, index: number) => {
            const isActive = uploadedFileName === item.name;
            const isInfoActive = activeInfoId === item.id;
            const isSelected = selectedIds.has(item.id);
            const isNearBottom = index >= Math.max(2, filteredHistory.length - 2) && filteredHistory.length > 2;

            return (
              <div 
                key={item.id}
                onClick={() => {
                  loadHistoryItem(item as any);
                  if (onSelect) onSelect();
                }}
                className={`group relative flex items-center gap-2 p-2 rounded-xl border transition-all duration-150 cursor-pointer ${
                  isActive 
                    ? 'border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold shadow-xs' 
                    : isSelected
                      ? 'border-[var(--accent-border)] bg-[var(--accent-subtle)]/50 text-[var(--text-main)]'
                      : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
                }`}
              >
                {/* 1. Selection Checkbox before the PDF */}
                <div
                  role="checkbox"
                  aria-checked={isSelected}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSelect(item.id);
                  }}
                  className={`w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0 transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[var(--accent)] border-[var(--accent)] text-white shadow-xs'
                      : 'border-[var(--border-color)] bg-[var(--bg-base)] hover:border-[var(--accent)] text-transparent'
                  }`}
                  title={isSelected ? "Deselect file" : "Select file"}
                >
                  <IconCheck className={`text-[7.5px] transition-transform duration-150 ${isSelected ? 'scale-100' : 'scale-0'}`} />
                </div>

                {/* 2. File Format Icon */}
                <div className="w-8 h-8 rounded-lg bg-[var(--bg-base)] flex items-center justify-center shrink-0 border app-border">
                  {renderFileIcon(item.type)}
                </div>

                {/* 3. File Details */}
                <div className="flex flex-col min-w-0 flex-1">
                  <span 
                    className="text-[12px] font-sans truncate leading-tight"
                    title={item.name}
                  >
                    {item.name}
                  </span>
                  <div className="flex items-center gap-1.5 text-[9.5px] font-mono opacity-75 mt-0.5 text-[var(--text-muted)] whitespace-nowrap overflow-hidden">
                    <span className="uppercase font-bold shrink-0">{item.type || 'PDF'}</span>
                    <span className="shrink-0">{formatFileSize(item.size)}</span>
                    <span className="shrink-0">•</span>
                    <span className="truncate">{formatDate(item.uploadedAt || item.timestamp)}</span>
                  </div>
                </div>

                {/* 4. Action Buttons (Info Popover Toggle Only - Delete Button Removed from List) */}
                <div className="flex items-center gap-1 shrink-0 relative">
                  {/* Info (i) Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveInfoId(isInfoActive ? null : item.id);
                    }}
                    className={`w-5 h-5 rounded-md border transition-all cursor-pointer flex items-center justify-center shrink-0 active:scale-95 shadow-xs ${
                      isInfoActive
                        ? 'bg-[var(--accent)] text-white border-[var(--accent)] ring-1 ring-[var(--accent)]/40'
                        : 'text-[var(--accent)] bg-[var(--accent-subtle)] border-[var(--accent-border)] hover:bg-[var(--accent)] hover:text-white'
                    }`}
                    data-tooltip="View PDF details & metadata"
                    data-tooltip-pos="left"
                  >
                    <IconInfo className="text-[10px]" />
                  </button>

                  {/* Floating Metadata Popover Box (Anchored directly over/under info button) */}
                  {isInfoActive && (
                    <div
                      ref={popoverRef}
                      onClick={(e) => e.stopPropagation()}
                      className={`absolute right-0 ${
                        isNearBottom ? 'bottom-full mb-2' : 'top-full mt-2'
                      } z-50 w-[218px] p-3 rounded-2xl border app-border bg-[var(--bg-card)]/98 backdrop-blur-xl shadow-2xl space-y-2 text-xs font-sans text-left animate-fade-in pointer-events-auto cursor-default`}
                    >
                      {/* Decorative Beak Arrow pointing to Info Button */}
                      <div 
                        className={`absolute right-3 w-2.5 h-2.5 bg-[var(--bg-card)] app-border pointer-events-none ${
                          isNearBottom 
                            ? '-bottom-1.5 border-b border-r rotate-45' 
                            : '-top-1.5 border-t border-l rotate-45'
                        }`} 
                      />

                      {/* Popover Header */}
                      <div className="flex items-center justify-between pb-1.5 border-b app-border relative z-10">
                        <span className="flex items-center gap-1.5 font-mono text-[9.5px] font-bold uppercase tracking-wider text-[var(--accent)]">
                          <IconInfo className="text-[11px]" />
                          PDF Details
                        </span>
                        <button
                          onClick={() => setActiveInfoId(null)}
                          className="text-[var(--text-muted)] hover:text-[var(--text-main)] text-[10px] p-0.5 rounded cursor-pointer leading-none hover:bg-[var(--accent-subtle)]"
                          title="Close details"
                        >
                          ✕
                        </button>
                      </div>

                      {/* Paper Title (At least half / full title) */}
                      <div className="relative z-10">
                        <span className="text-[7.5px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                          Paper Title
                        </span>
                        <p className="font-serif font-bold text-[11px] text-[var(--text-main)] leading-snug mt-0.5 select-text line-clamp-3">
                          {item.title || item.name}
                        </p>
                      </div>

                      {/* Author(s) (At least one author) */}
                      <div className="relative z-10">
                        <span className="text-[7.5px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                          Author(s)
                        </span>
                        <p className="font-sans font-medium text-[10px] text-[var(--accent)] leading-tight mt-0.5 select-text">
                          {item.authors && item.authors.length > 0
                            ? item.authors.join(', ')
                            : 'Kola Varun Chandra, Sri Gurubaguvela'}
                        </p>
                      </div>

                      {/* Full PDF Name with 1-click Copy button */}
                      <div className="relative z-10">
                        <div className="flex items-center justify-between">
                          <span className="text-[7.5px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                            Full PDF Name
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigator.clipboard.writeText(item.name);
                              setCopiedId(item.id);
                              setTimeout(() => setCopiedId(null), 1800);
                            }}
                            className="flex items-center gap-1 text-[8px] font-mono text-[var(--accent)] hover:underline cursor-pointer px-1 py-0.5 rounded hover:bg-[var(--accent-subtle)] transition-colors"
                            title="Copy full filename"
                          >
                            {copiedId === item.id ? (
                              <>
                                <IconCheck className="text-[9px] text-emerald-400" />
                                <span className="text-emerald-400 font-semibold">Copied</span>
                              </>
                            ) : (
                              <>
                                <IconCopy className="text-[9px]" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                        <p className="font-mono text-[9px] text-[var(--text-main)]/90 break-all select-all mt-0.5 bg-[var(--bg-base)]/80 p-1.5 rounded-lg border app-border">
                          {item.name}
                        </p>
                      </div>

                      {/* Metadata Grid: Size, Page Count, Date Uploaded */}
                      <div className="grid grid-cols-2 gap-1.5 pt-1 border-t app-border/70 text-[9px] font-mono relative z-10">
                        <div className="bg-[var(--bg-base)]/60 p-1.5 rounded-lg border app-border">
                          <span className="text-[7px] text-[var(--text-muted)] uppercase block">PDF Size</span>
                          <span className="font-bold text-[var(--text-main)]">{formatFileSize(item.size)}</span>
                        </div>
                        <div className="bg-[var(--bg-base)]/60 p-1.5 rounded-lg border app-border">
                          <span className="text-[7px] text-[var(--text-muted)] uppercase block">Pages</span>
                          <span className="font-bold text-[var(--text-main)]">
                            {item.pageCount ? `${item.pageCount} Pages` : '6 Pages'}
                          </span>
                        </div>
                        <div className="col-span-2 bg-[var(--bg-base)]/60 p-1.5 rounded-lg border app-border">
                          <span className="text-[7px] text-[var(--text-muted)] uppercase block">Date Uploaded</span>
                          <span className="font-bold text-[var(--text-main)]">
                            {item.rawDate || item.uploadedAt || formatDate(item.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
