export {};

declare global {
  interface MascotAPI {
    getPathForFile: (file: File) => string;
    setIgnoreMouseEvents: (ignore: boolean, options?: any) => void;
    dragWindow: (delta: { deltaX: number; deltaY: number }) => void;
    dragEnd: () => void;
    togglePanel: () => void;
    uploadPDF: (filePath: string, type: 'pdf' | 'docx') => void;
    openFileSelector: (type: 'pdf' | 'docx') => void;
    onUploadStatus: (callback: (status: { success: boolean; filename: string; type: 'pdf' | 'docx'; error?: string }) => void) => void;
    onFileSelected: (callback: (data: any) => void) => void;
    onStateChange: (callback: (state: string) => void) => void;
    onPipelineLog: (callback: (log: { text: string; type?: string }) => void) => void;
    onPipelineCompleted: (callback: (status: { success: boolean; filename?: string; type?: 'pdf' | 'docx'; reportContent?: string; error?: string }) => void) => void;
  }

  interface Window {
    mascotAPI?: MascotAPI;
  }
}
