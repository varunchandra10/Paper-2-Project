import React, { useRef, useState } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaFilePdf, FaFileWord } from 'react-icons/fa6';
import { FiLoader, FiUploadCloud } from 'react-icons/fi';

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
        className={`relative flex-1 border-2 border-dashed rounded-xl p-3.5 flex flex-col items-center justify-center text-center transition-all duration-200 select-none group outline-none focus-visible:ring-2 focus-visible:ring-brass/80 ${
          isAnalyzing 
            ? 'opacity-50 cursor-not-allowed border-border/30 bg-muted/20' 
            : isPdfOver
              ? 'border-brass bg-brass/10 shadow-[0_0_18px_rgba(212,163,56,0.2)] -translate-y-0.5'
              : 'border-border bg-card/60 hover:border-brass/60 hover:bg-brass/5 hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]'
        }`}
      >
        <div className="relative mb-2 flex items-center justify-center">
          {isAnalyzing ? (
            <FiLoader className="text-xl text-brass animate-spin" />
          ) : (
            <FaFilePdf className={`text-2xl transition-transform duration-200 group-hover:scale-110 ${
              isPdfOver ? 'text-brass' : 'text-brass/80 group-hover:text-brass'
            }`} />
          )}
        </div>
        <span className="text-xs font-mono font-bold tracking-tight text-foreground">
          Paper (PDF)
        </span>
        <span className="text-[10px] font-mono text-muted-foreground mt-0.5 flex items-center gap-1">
          <FiUploadCloud className="text-[10px]" /> Drop or browse
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
        className={`relative flex-1 border-2 border-dashed rounded-xl p-3.5 flex flex-col items-center justify-center text-center transition-all duration-200 select-none group outline-none focus-visible:ring-2 focus-visible:ring-brass/80 ${
          isAnalyzing 
            ? 'opacity-50 cursor-not-allowed border-border/30 bg-muted/20' 
            : isDocxOver
              ? 'border-brass bg-brass/10 shadow-[0_0_18px_rgba(212,163,56,0.2)] -translate-y-0.5'
              : 'border-border bg-card/60 hover:border-brass/60 hover:bg-brass/5 hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]'
        }`}
      >
        <div className="relative mb-2 flex items-center justify-center">
          {isAnalyzing ? (
            <FiLoader className="text-xl text-brass animate-spin" />
          ) : (
            <FaFileWord className={`text-2xl transition-transform duration-200 group-hover:scale-110 ${
              isDocxOver ? 'text-brass' : 'text-brass/80 group-hover:text-brass'
            }`} />
          )}
        </div>
        <span className="text-xs font-mono font-bold tracking-tight text-foreground">
          Context (DOCX)
        </span>
        <span className="text-[10px] font-mono text-muted-foreground mt-0.5 flex items-center gap-1">
          <FiUploadCloud className="text-[10px]" /> Drop or browse
        </span>
      </div>
    </div>
  );
};