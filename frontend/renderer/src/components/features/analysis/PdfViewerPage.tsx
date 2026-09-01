import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { IconBack, IconPdf } from '../../ui/Icons';

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
          className="p-2 rounded-xl border app-border bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-all cursor-pointer flex items-center justify-center active:scale-95 shadow-xs"
          title="Return to Chat"
        >
          <IconBack className="text-base" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full h-full flex flex-col overflow-hidden bg-[var(--bg-base)] text-[var(--text-main)]">

      {/* ── Slim inline nav strip — icon-only back + filename, no full top bar ── */}
      <div className="flex items-center gap-3 px-4 py-2 border-b app-border bg-[var(--bg-base)] shrink-0">
        <button
          onClick={handleBack}
          className="p-2 rounded-xl border app-border bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-all cursor-pointer flex items-center justify-center active:scale-95 shadow-xs"
          title="Return to Chat"
        >
          <IconBack className="text-base" />
        </button>

        <div className="flex items-center gap-1.5 min-w-0">
          <IconPdf className="text-[var(--accent)] text-xs shrink-0" />
          <span className="text-[11px] font-mono font-semibold text-[var(--text-muted)] truncate max-w-[400px]">
            {uploadedFileName || `${activePaperId}.pdf`}
          </span>
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
