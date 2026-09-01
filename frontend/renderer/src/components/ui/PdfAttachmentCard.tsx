import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { IconPdf, IconWord, IconDoc, IconColor } from './Icons';

interface PdfAttachmentCardProps {
  filename: string;
  paperId: string;
}

interface FileTypeConfig {
  icon: React.ReactNode;
  color: string;
}

const getFileConfig = (ext: string): FileTypeConfig => {
  switch (ext.toLowerCase()) {
    case 'pdf':
      return {
        icon: <IconPdf className={`text-3xl ${IconColor.accent}`} />,
        color: IconColor.accent,
      };
    case 'docx':
      return {
        icon: <IconWord className={`text-3xl ${IconColor.accent}`} />,
        color: IconColor.accent,
      };
    case 'doc':
      return {
        icon: <IconDoc className={`text-3xl ${IconColor.accent}`} />,
        color: IconColor.accent,
      };
    default:
      return {
        icon: <IconDoc className={`text-3xl ${IconColor.muted}`} />,
        color: IconColor.muted,
      };
  }
};

export const PdfAttachmentCard: React.FC<PdfAttachmentCardProps> = ({
  filename,
  paperId,
}) => {
  const { setActivePaperId, setActiveView } = usePanelStore();

  const lastDotIdx = filename.lastIndexOf('.');
  const extRaw = lastDotIdx > 0 ? filename.slice(lastDotIdx + 1) : 'file';
  const cfg = getFileConfig(extRaw);

  // Show at least half the name — truncate only if very long
  const halfLen = Math.ceil(filename.length / 2);
  const keepLen = Math.max(halfLen, 10);
  const displayName =
    filename.length > keepLen + 4
      ? filename.slice(0, keepLen) + '…' + filename.slice(lastDotIdx)
      : filename;

  const handleOpen = () => {
    setActivePaperId(paperId);
    setActiveView('pdf-viewer');
  };

  return (
    <div
      onClick={handleOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleOpen();
        }
      }}
      title={`Open ${filename}`}
      className="cursor-pointer select-none outline-none group flex flex-col items-center gap-1 hover:opacity-75 active:scale-95 transition-all duration-150"
    >
      {/* File Icon */}
      <div className="transition-transform duration-150 group-hover:scale-110">
        {cfg.icon}
      </div>

      {/* Filename below icon */}
      <span className={`text-[10px] font-mono font-semibold ${cfg.color} max-w-[120px] text-center leading-tight break-all`}>
        {displayName}
      </span>
    </div>
  );
};