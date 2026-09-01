import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaFilePdf } from 'react-icons/fa6';
import { FiExternalLink } from 'react-icons/fi';

interface PdfAttachmentCardProps {
  filename: string;
  paperId: string;
}

export const PdfAttachmentCard: React.FC<PdfAttachmentCardProps> = ({
  filename,
  paperId,
}) => {
  const { setActivePaperId, setActiveView } = usePanelStore();
  const truncated =
    filename.length > 28 ? filename.slice(0, 22) + '…' + filename.slice(-5) : filename;

  const handleOpen = () => {
    setActivePaperId(paperId);
    setActiveView('pdf-viewer');
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    handleOpen();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleOpen();
    }
  };

  return (
    <div
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      className="group flex items-stretch gap-0 rounded-2xl overflow-hidden border border-black/10 bg-white text-slate-900 shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-all duration-200 cursor-pointer no-underline shrink-0 select-none outline-none hover:shadow-[0_6px_20px_rgba(0,0,0,0.18)]"
      title={`Open ${filename} in PDF Reader`}
    >
      {/* Left: PDF Document Preview Thumbnail */}
      <div className="w-12 flex flex-col items-center justify-center px-2 py-2 shrink-0 bg-slate-50 border-r border-slate-100 group-hover:bg-sky-50/60 transition-colors duration-200">
        <div className="relative w-7 h-9 rounded bg-white border border-slate-200 flex flex-col justify-between p-1 overflow-hidden shadow-2xs transition-colors">
          {/* Top PDF Badge / Icon */}
          <div className="flex items-center justify-between w-full">
            <FaFilePdf className="text-[10px] text-sky-600" />
            <div className="w-1.5 h-1.5 rounded-full bg-sky-500/40 group-hover:bg-sky-500 transition-colors" />
          </div>

          {/* Simulated Text Lines */}
          <div className="flex flex-col gap-0.5 my-auto">
            <div className="h-0.5 w-[85%] rounded-full bg-slate-300 group-hover:bg-sky-400 transition-colors" />
            <div className="h-0.5 w-[60%] rounded-full bg-slate-200 group-hover:bg-sky-300 transition-colors" />
            <div className="h-0.5 w-[75%] rounded-full bg-slate-200 group-hover:bg-sky-300 transition-colors" />
          </div>

          {/* Academic Dog-ear Corner Fold */}
          <div className="absolute top-0 right-0 w-2 h-2 bg-slate-100 border-b border-l border-slate-200 rounded-bl" />
        </div>
      </div>

      {/* Right: Filename + Metadata */}
      <div className="flex flex-col justify-center px-3 py-2 gap-0.5 min-w-0 font-mono">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-bold tracking-tight text-slate-900 group-hover:text-sky-600 transition-colors truncate max-w-[160px]">
            {truncated}
          </span>
          <FiExternalLink className="text-[10px] text-slate-400 group-hover:text-sky-600 shrink-0 transition-colors" />
        </div>
        <span className="text-[9px] font-bold uppercase tracking-widest text-sky-600 flex items-center gap-1">
          <span>PDF ATTACHMENT</span>
          <span className="text-[8px] text-slate-400 font-sans font-normal">
            · TAP TO VIEW
          </span>
        </span>
      </div>
    </div>
  );
};