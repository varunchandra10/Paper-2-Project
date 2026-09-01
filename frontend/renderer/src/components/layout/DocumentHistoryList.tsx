import React, { useState, useMemo, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { SkinLoader } from '../ui/SkinLoader';
import { 
  FaFilePdf, 
  FaFileWord, 
  FaTrash, 
  FaTimes, 
  FaFileAlt, 
  FaSearch 
} from 'react-icons/fa';
import { BsBoxArrowUpRight } from 'react-icons/bs';

interface HistoryItem {
  id: string;
  name: string;
  type: string;
  size?: string | number;
  uploadedAt?: string;
}

export const DocumentHistoryList: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  const { 
    uploadedHistory, 
    uploadedFileName, 
    loadHistoryItem, 
    deleteHistoryItem,
    fetchUploadedPapers,
    isPapersLoading,
    setActivePaperId,
    setActiveView
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
        return <FaFilePdf className="text-red-400 text-lg group-hover:scale-110 transition-transform duration-200" />;
      case 'docx':
      case 'doc':
      case 'word':
        return <FaFileWord className="text-sky-400 text-lg group-hover:scale-110 transition-transform duration-200" />;
      default:
        return <FaFileAlt className="text-amber-400 text-lg group-hover:scale-110 transition-transform duration-200" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden select-none">
      {/* Search Input Filter */}
      <div className="px-3 pt-2.5 pb-2 shrink-0 font-mono">
        <div className="relative w-full">
          <FaSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-[10px]" />
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
              <FaTimes />
            </button>
          )}
        </div>
      </div>

      {/* Document Items Grid List */}
      <div className="flex-1 overflow-y-auto px-2.5 py-1 space-y-1.5 scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent">
        {isPapersLoading ? (
          <SkinLoader type="document" />
        ) : filteredHistory.length === 0 ? (
          <div className="py-8 flex flex-col items-center justify-center text-center p-3 rounded-xl border border-dashed app-border bg-[var(--bg-base)] font-sans">
            <FaFileAlt className="text-[var(--text-muted)] text-xl mb-1.5" />
            <span className="text-[11px] text-[var(--text-muted)]">
              {searchQuery ? 'No documents match search' : 'No research papers uploaded'}
            </span>
          </div>
        ) : (
          filteredHistory.map((item: HistoryItem) => {
            const isActive = uploadedFileName === item.name;
            const paperId = item.id.startsWith('paper_') ? item.id : `paper_${item.name.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase()}`;

            return (
              <div 
                key={item.id}
                onClick={() => loadHistoryItem(item as any)}
                className={`group relative flex items-center gap-2 p-2 rounded-xl border transition-all duration-150 cursor-pointer overflow-hidden ${
                  isActive 
                    ? 'border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold shadow-xs' 
                    : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] hover:border-[var(--accent-border)]'
                }`}
              >
                {/* File Format Icon */}
                <div className="w-8 h-8 rounded-lg bg-[var(--bg-base)] flex items-center justify-center shrink-0 border app-border">
                  {renderFileIcon(item.type)}
                </div>

                {/* File Details */}
                <div className="flex flex-col min-w-0 flex-1">
                  <span 
                    className="text-[12px] font-sans truncate leading-tight"
                    title={item.name}
                  >
                    {item.name}
                  </span>
                  <div className="flex items-center gap-1.5 text-[9.5px] font-mono opacity-70 mt-0.5 text-[var(--text-muted)]">
                    <span className="uppercase font-bold">{item.type || 'PDF'}</span>
                    <span>•</span>
                    <span>{formatFileSize(item.size)}</span>
                  </div>
                </div>

                {/* Action Buttons (Always visible / sticked) */}
                <div className="flex items-center gap-1 shrink-0">
                  {/* View PDF Button (Icon-only with BsBoxArrowUpRight) */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      loadHistoryItem(item as any);
                      setActivePaperId(paperId);
                      setActiveView('pdf-viewer');
                    }}
                    className="p-1.5 rounded-lg text-[var(--accent)] bg-[var(--accent-subtle)] border border-[var(--accent-border)] hover:bg-[var(--accent)] hover:text-white transition-all cursor-pointer flex items-center justify-center shrink-0 active:scale-95 shadow-xs"
                    title="View PDF in embedded reader"
                  >
                    <BsBoxArrowUpRight className="text-xs" />
                  </button>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryItem(item.id);
                    }}
                    className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all cursor-pointer shrink-0"
                    title="Delete document"
                  >
                    <FaTrash className="text-xs" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
