import React, { useRef, useState } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { IconPdf, IconWord, IconLoader, IconUploadCloud, IconColor } from './Icons';

export const DropZone: React.FC = () => {
  const { uploadPaper, isAnalyzing, selectedModel } = usePanelStore();
  const [isPdfOver, setIsPdfOver] = useState(false);
  const [isDocxOver, setIsDocxOver] = useState(false);

  const pdfInputRef = useRef<HTMLInputElement>(null);
  const docxInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent, type: 'pdf' | 'docx') => {
    e.preventDefault();
    if (isAnalyzing) return;
    if (type === 'pdf') setIsPdfOver(true);
    else setIsDocxOver(true);
  };

  const handleDragLeave = (type: 'pdf' | 'docx') => {
    if (type === 'pdf') setIsPdfOver(false);
    else setIsDocxOver(false);
  };

  const processFile = (file: File, type: 'pdf' | 'docx') => {
    if (window.mascotAPI?.getPathForFile) {
      // Electron runtime
      const filePath = window.mascotAPI.getPathForFile(file);
      window.mascotAPI.uploadPDF(filePath, type, selectedModel);
    } else {
      // Web browser runtime
      uploadPaper(file);
    }
  };

  const handleDrop = (e: React.DragEvent, type: 'pdf' | 'docx') => {
    e.preventDefault();
    if (isAnalyzing) return;
    setIsPdfOver(false);
    setIsDocxOver(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFile(files[0], type);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'pdf' | 'docx') => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0], type);
    }
  };

  const triggerPicker = (type: 'pdf' | 'docx') => {
    if (isAnalyzing) return;
    if (window.mascotAPI?.openFileSelector) {
      window.mascotAPI.openFileSelector(type, selectedModel);
    } else {
      if (type === 'pdf') pdfInputRef.current?.click();
      else docxInputRef.current?.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, type: 'pdf' | 'docx') => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      triggerPicker(type);
    }
  };

  return (
    <div className="flex gap-3 w-full">
      {/* Hidden File Inputs */}
      <input 
        type="file" 
        ref={pdfInputRef} 
        accept=".pdf" 
        className="hidden" 
        onChange={(e) => handleFileChange(e, 'pdf')} 
      />
      <input 
        type="file" 
        ref={docxInputRef} 
        accept=".docx,.doc" 
        className="hidden" 
        onChange={(e) => handleFileChange(e, 'docx')} 
      />

      {/* PDF Dropzone */}
      <div
        onClick={() => triggerPicker('pdf')}
        onKeyDown={(e) => handleKeyDown(e, 'pdf')}
        onDragOver={(e) => handleDragOver(e, 'pdf')}
        onDragLeave={() => handleDragLeave('pdf')}
        onDrop={(e) => handleDrop(e, 'pdf')}
        aria-disabled={isAnalyzing}
        role="button"
        tabIndex={isAnalyzing ? -1 : 0}
        className={`relative flex-1 border-2 border-dashed rounded-xl p-3.5 flex flex-col items-center justify-center text-center transition-all duration-200 select-none group outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] ${
          isAnalyzing 
            ? 'opacity-50 cursor-not-allowed border-border/30 bg-muted/20' 
            : isPdfOver
              ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-[0_0_18px_rgba(0,0,0,0.1)] -translate-y-0.5'
              : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:border-[var(--accent)] hover:bg-[var(--accent-subtle)] hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]'
        }`}
      >
        <div className="relative mb-2 flex items-center justify-center">
          {isAnalyzing ? (
            <IconLoader className={`text-xl ${IconColor.accent} animate-spin`} />
          ) : (
            <IconPdf className={`text-2xl transition-transform duration-200 group-hover:scale-110 ${
              isPdfOver ? IconColor.accent : 'text-[var(--accent)]'
            }`} />
          )}
        </div>
        <span className="text-xs font-mono font-bold tracking-tight text-[var(--text-main)]">
          Paper (PDF)
        </span>
        <span className="text-[10px] font-mono text-[var(--text-muted)] mt-0.5 flex items-center gap-1">
          <IconUploadCloud className="text-[10px]" /> Drop or browse
        </span>
      </div>

      {/* DOCX Dropzone */}
      <div
        onClick={() => triggerPicker('docx')}
        onKeyDown={(e) => handleKeyDown(e, 'docx')}
        onDragOver={(e) => handleDragOver(e, 'docx')}
        onDragLeave={() => handleDragLeave('docx')}
        onDrop={(e) => handleDrop(e, 'docx')}
        aria-disabled={isAnalyzing}
        role="button"
        tabIndex={isAnalyzing ? -1 : 0}
        className={`relative flex-1 border-2 border-dashed rounded-xl p-3.5 flex flex-col items-center justify-center text-center transition-all duration-200 select-none group outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] ${
          isAnalyzing 
            ? 'opacity-50 cursor-not-allowed border-border/30 bg-muted/20' 
            : isDocxOver
              ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-[0_0_18px_rgba(0,0,0,0.1)] -translate-y-0.5'
              : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:border-[var(--accent)] hover:bg-[var(--accent-subtle)] hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]'
        }`}
      >
        <div className="relative mb-2 flex items-center justify-center">
          {isAnalyzing ? (
            <IconLoader className={`text-xl ${IconColor.accent} animate-spin`} />
          ) : (
            <IconWord className={`text-2xl transition-transform duration-200 group-hover:scale-110 ${
              isDocxOver ? IconColor.accent : 'text-[var(--accent)]'
            }`} />
          )}
        </div>
        <span className="text-xs font-mono font-bold tracking-tight text-[var(--text-main)]">
          Context (DOCX)
        </span>
        <span className="text-[10px] font-mono text-[var(--text-muted)] mt-0.5 flex items-center gap-1">
          <IconUploadCloud className="text-[10px]" /> Drop or browse
        </span>
      </div>
    </div>
  );
};