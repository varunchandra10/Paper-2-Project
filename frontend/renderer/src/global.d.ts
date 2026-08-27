export {};

declare global {
  interface MascotAPI {
    getPathForFile: (file: File) => string;
    setIgnoreMouseEvents: (ignore: boolean, options?: any) => void;
    dragWindow: (delta: { deltaX: number; deltaY: number }) => void;
    dragEnd: () => void;
    togglePanel: () => void;
    uploadPDF: (filePath: string, type: 'pdf' | 'docx', modelName?: string) => void;
    openFileSelector: (type: 'pdf' | 'docx', modelName?: string) => void;
    triggerUpload: (filename: string, filePath: string, type: 'pdf' | 'docx', modelName?: string) => void;
    onUploadStatus: (callback: (status: { success: boolean; filename: string; type: 'pdf' | 'docx'; filePath?: string; error?: string }) => void) => void;
    onFileStaged: (callback: (data: { success: boolean; filename: string; type: 'pdf' | 'docx'; filePath: string; modelName?: string; error?: string }) => void) => void;
    onFileSelected: (callback: (data: any) => void) => void;
    onStateChange: (callback: (state: string) => void) => void;
    onPipelineLog: (callback: (log: { text: string; type?: string }) => void) => void;
    onPipelineCompleted: (callback: (status: { success: boolean; filename?: string; type?: 'pdf' | 'docx'; reportContent?: string; error?: string }) => void) => void;
    toggleMaximize: () => void;
    onMaximizeChange: (callback: (isMaximized: boolean) => void) => void;
  }

  interface Window {
    mascotAPI?: MascotAPI;
  }
}
