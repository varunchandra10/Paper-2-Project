import React, { useRef, useState } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FaFilePdf, FaFileWord } from 'react-icons/fa6';

export const DropZone: React.FC = () => {
  const { triggerUpload, isAnalyzing, selectedModel } = usePanelStore();
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

  const handleDrop = (e: React.DragEvent, type: 'pdf' | 'docx') => {
    e.preventDefault();
    if (isAnalyzing) return;
    setIsPdfOver(false);
    setIsDocxOver(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (window.mascotAPI?.getPathForFile) {
        const filePath = window.mascotAPI.getPathForFile(file);
        window.mascotAPI.uploadPDF(filePath, type, selectedModel);
      } else {
        triggerUpload(file.name, type);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'pdf' | 'docx') => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (window.mascotAPI?.getPathForFile) {
        const filePath = window.mascotAPI.getPathForFile(file);
        window.mascotAPI.uploadPDF(filePath, type, selectedModel);
      } else {
        triggerUpload(file.name, type);
      }
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

  return (
    <div className="flex gap-3">
      {/* Hidden file browsers */}
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

      {/* PDF dropzone */}
      <div
        onClick={() => triggerPicker('pdf')}
        onDragOver={(e) => handleDragOver(e, 'pdf')}
        onDragLeave={() => handleDragLeave('pdf')}
        onDrop={(e) => handleDrop(e, 'pdf')}
        className={`flex-1 border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 transform select-none ${
          isAnalyzing 
            ? 'opacity-40 cursor-not-allowed border-border/5 bg-black/5' 
            : isPdfOver
              ? 'border-brass bg-brass/10 -translate-y-0.5 shadow-md scale-102'
              : 'border-border bg-black/10 hover:border-brass/50 hover:bg-foreground/5 hover:-translate-y-0.5'
        }`}
        role="button"
        tabIndex={0}
      >
        <FaFilePdf className="text-2xl text-brass/75 mb-2 transition-transform duration-300" />
        <span className="text-[10px] font-bold text-foreground">Paper (PDF)</span>
        <span className="text-[7.5px] text-muted-foreground mt-0.5">Drop or browse</span>
      </div>

      {/* DOCX dropzone */}
      <div
        onClick={() => triggerPicker('docx')}
        onDragOver={(e) => handleDragOver(e, 'docx')}
        onDragLeave={() => handleDragLeave('docx')}
        onDrop={(e) => handleDrop(e, 'docx')}
        className={`flex-1 border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 transform select-none ${
          isAnalyzing 
            ? 'opacity-40 cursor-not-allowed border-border/5 bg-black/5' 
            : isDocxOver
              ? 'border-brass bg-brass/10 -translate-y-0.5 shadow-md scale-102'
              : 'border-border bg-black/10 hover:border-brass/50 hover:bg-foreground/5 hover:-translate-y-0.5'
        }`}
        role="button"
        tabIndex={0}
      >
        <FaFileWord className="text-2xl text-brass/75 mb-2 transition-transform duration-300" />
        <span className="text-[10px] font-bold text-foreground">Context (DOCX)</span>
        <span className="text-[7.5px] text-muted-foreground mt-0.5">Drop or browse</span>
      </div>
    </div>
  );
};
