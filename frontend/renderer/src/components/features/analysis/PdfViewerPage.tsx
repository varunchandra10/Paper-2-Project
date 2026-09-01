import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { FaArrowLeft, FaRegFilePdf } from 'react-icons/fa6';

export const PdfViewerPage: React.FC = () => {
  const { activePaperId, uploadedFileName, setActiveView } = usePanelStore();

  const handleBack = () => {
    setActiveView('chat');
  };

  const getPdfUrl = () => {
    if (!activePaperId) return '';
    const apiBase = (typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:'))
      ? 'http://localhost:8000'
      : '/api';
    return `${apiBase}/papers/${activePaperId}/pdf#toolbar=1&navpanes=0`;
  };

  if (!activePaperId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-3">
        <span className="text-xs font-mono text-[var(--text-muted)]">No PDF selected.</span>
        <button
          onClick={handleBack}
          className="text-[10px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-4 py-2 rounded-xl transition-all"
        >
          Return to Chat
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full h-full flex flex-col overflow-hidden bg-[var(--bg-base)] text-[var(--text-main)]">
      {/* ── Premium Header Navigation ── */}
      <div className="h-14 px-6 border-b app-border flex justify-between items-center bg-[var(--bg-card)] shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-[10px] font-mono font-bold bg-[var(--bg-base)] hover:bg-[var(--accent)] hover:text-white text-[var(--text-main)] border app-border px-3.5 py-1.5 rounded-xl transition-all duration-200 cursor-pointer shadow-xs"
          >
            <FaArrowLeft className="text-[10px]" />
            BACK TO WORKSPACE
          </button>
          
          <div className="flex items-center gap-2 border-l app-border pl-4">
            <FaRegFilePdf className="text-[var(--accent)] text-sm shrink-0" />
            <span className="text-[11px] font-mono font-semibold text-[var(--text-main)] truncate max-w-[400px]">
              {uploadedFileName || `${activePaperId}.pdf`}
            </span>
          </div>
        </div>

        <div className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] px-2 py-0.5 rounded-full select-none">
          EMBEDDED READER
        </div>
      </div>

      {/* ── Main Embed Viewport ── */}
      <div className="flex-1 w-full bg-[var(--bg-base)] p-3 flex">
        <iframe
          src={getPdfUrl()}
          title="PDF Document Viewer"
          className="w-full h-full rounded-xl border app-border bg-[var(--bg-card)] shadow-2xl"
          style={{ border: 'none' }}
        />
      </div>
    </div>
  );
};
