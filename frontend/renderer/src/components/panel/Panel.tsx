import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { useLogsStore } from '../../store/logsStore';
import { ThemeToggle } from '../theme/ThemeToggle';
import { DropZone } from './DropZone';
import { MilestoneTracker } from './MilestoneTracker';
import { StatsCharts } from './StatsCharts';
import { TierSelector } from './TierSelector';
import { ReportView } from './ReportView';
import { LogsDrawer } from '../logs/LogsDrawer';
import { DocumentsDrawer } from './DocumentsDrawer';
import { FaFilePdf, FaFileWord } from 'react-icons/fa6';
import { FaTimes } from "react-icons/fa";
import { BiSolidTerminal } from "react-icons/bi";

export const Panel: React.FC = () => {
  const { 
    isPanelOpen, 
    togglePanel, 
    uploadedFileName, 
    uploadedFileType, 
    resetAnalysis,
    toggleLogs,
    isLogsOpen,
    toggleHistory,
    isHistoryOpen
  } = usePanelStore();

  React.useEffect(() => {
    // ... [Keep your existing useEffect logic intact] ...
    if (window.mascotAPI?.onUploadStatus) {
      window.mascotAPI.onUploadStatus((status) => {
        if (status.success) {
          usePanelStore.getState().startAnalysis(status.filename, status.type);
        } else {
          const { addLog } = useLogsStore.getState();
          addLog(`[Error] Ingestion failed: ${status.error}`, 'error');
        }
      });
    }

    if (window.mascotAPI?.onPipelineLog) {
      window.mascotAPI.onPipelineLog((log) => {
        const { addLog } = useLogsStore.getState();
        const logText = log.text;
        let type: 'info' | 'success' | 'warning' | 'error' | 'system' = 'info';

        if (logText.includes('[Success]')) type = 'success';
        else if (logText.includes('[System]')) type = 'system';
        else if (logText.includes('[Error]')) type = 'error';
        else if (logText.includes('[Warning]')) type = 'warning';

        addLog(logText, type);

        if (logText.includes('Step 1')) usePanelStore.getState().setMilestoneActive(0);
        else if (logText.includes('Step 2')) usePanelStore.getState().setMilestoneActive(1);
        else if (logText.includes('Step 3')) usePanelStore.getState().setMilestoneActive(2);
        else if (logText.includes('Step 4')) usePanelStore.getState().setMilestoneActive(3);
        else if (logText.includes('Step 5')) usePanelStore.getState().setMilestoneActive(4);
      });
    }

    if (window.mascotAPI?.onPipelineCompleted) {
      window.mascotAPI.onPipelineCompleted((result) => {
        if (result.success && result.reportContent) {
          usePanelStore.getState().completeAnalysis(result.reportContent);
        } else {
          usePanelStore.getState().failAnalysis(result.error || 'Pipeline execution failed');
        }
      });
    }
  }, []);

  if (!isPanelOpen) return null;

  return (
    <div className="relative w-full h-full flex flex-col bg-background border-l border-border/30 shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)] select-none text-foreground font-sans overflow-hidden">
      
      {/* High-Tech Dot Grid Background Overlay */}
      <div className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(circle,currentColor_1px,transparent_1px)] [background-size:16px_16px]" />

      {/* Floating Glassmorphism Command Bar */}
      <header className="sticky top-2 z-10 mx-3 mt-2 px-5 py-3 rounded-xl border border-border/40 bg-background/60 backdrop-blur-2xl shadow-lg flex justify-between items-center relative overflow-hidden">
        {/* Decorative glowing accent line at the bottom of header */}
        <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brass/50 to-transparent" />
        
        <div className="flex flex-col">
          <h1 className="m-0 text-[13px] font-black tracking-[0.2em] uppercase font-mono bg-gradient-to-r from-brass via-brass/80 to-foreground text-transparent bg-clip-text drop-shadow-[0_0_8px_rgba(var(--brass),0.3)]">
            Paper_2_Project
          </h1>
          <span className="text-[8px] tracking-[0.3em] font-mono text-muted-foreground uppercase opacity-70">
            SYS.PIPELINE.ACTIVE
          </span>
        </div>
        
        <div className="flex items-center gap-2.5 z-10">
          <ThemeToggle />

          {/* Tech-styled History Button */}
          <button 
            onClick={toggleHistory}
            className={`group relative p-2 rounded-md transition-all duration-300 overflow-hidden border ${
              isHistoryOpen 
                ? 'border-red-500/50 bg-red-500/10 shadow-[inset_0_0_12px_rgba(239,68,68,0.2)]' 
                : 'border-transparent hover:border-red-500/30 hover:bg-red-500/5'
            }`}
            title="Database Records"
            aria-label="Toggle Document History"
          >
            <FaFilePdf className={`text-sm relative z-10 transition-colors ${isHistoryOpen ? 'text-red-500' : 'text-foreground/50 group-hover:text-red-500'}`} />
          </button>

          {/* Tech-styled Logs Button */}
          <button 
            onClick={toggleLogs}
            className={`group relative p-2 rounded-md transition-all duration-300 overflow-hidden border ${
              isLogsOpen 
                ? 'border-amber-400/50 bg-amber-400/10 shadow-[inset_0_0_12px_rgba(251,191,36,0.2)]' 
                : 'border-transparent hover:border-amber-400/30 hover:bg-amber-400/5'
            }`}
            title="System Terminal"
            aria-label="Toggle Console Logs"
          >
            <BiSolidTerminal className={`text-sm relative z-10 transition-colors ${isLogsOpen ? 'text-amber-400' : 'text-foreground/50 group-hover:text-amber-400'}`} />
          </button>

          {/* Aggressive Close Button */}
          <button 
            onClick={() => window.mascotAPI ? window.mascotAPI.togglePanel() : togglePanel()}
            className="ml-2 p-1.5 text-foreground/30 hover:text-red-500 hover:bg-red-500/10 hover:shadow-[0_0_10px_rgba(239,68,68,0.2)] rounded-md transition-all duration-200 active:scale-90"
            title="Terminate Process"
          >
            <FaTimes className="text-lg" />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-6 pt-8 flex flex-col gap-10 scrollbar-thin scrollbar-thumb-brass/20 scrollbar-track-transparent z-10 relative">
        
        {/* Upload triggers or active file stats card */}
        {!uploadedFileName ? (
          <DropZone />
        ) : (
          <div className="group relative bg-black/40 border border-border/30 rounded-r-lg border-l-4 border-l-brass p-4 flex justify-between items-center shadow-lg hover:shadow-[0_0_20px_-5px_rgba(var(--brass),0.3)] transition-all duration-500 overflow-hidden backdrop-blur-md">
            {/* Animated scanning background element */}
            <div className="absolute inset-0 bg-gradient-to-r from-brass/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
            
            <div className="flex items-center gap-4 relative z-10">
              <div className="p-2.5 bg-background/50 rounded-md shadow-inner border border-border/40">
                {uploadedFileType === 'pdf' ? (
                  <FaFilePdf className="text-brass text-xl drop-shadow-[0_0_5px_rgba(var(--brass),0.5)]" />
                ) : (
                  <FaFileWord className="text-blue-400 text-xl drop-shadow-[0_0_5px_rgba(96,165,250,0.5)]" />
                )}
              </div>
              <div className="flex flex-col truncate">
                <span className="text-[9px] font-mono font-bold text-brass uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-brass rounded-full animate-pulse" />
                  Target Acquired
                </span>
                <span className="text-sm font-medium text-foreground/90 truncate max-w-[200px] font-sans">
                  {uploadedFileName}
                </span>
              </div>
            </div>
            <button 
              onClick={resetAnalysis} 
              className="relative z-10 p-2 text-foreground/40 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-all duration-200 active:scale-90 border border-transparent hover:border-red-400/20"
              title="Eject Source"
            >
              <FaTimes className="text-sm" />
            </button>
          </div>
        )}

        {/* Blueprint Milestones */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-3 opacity-80">
            <h2 className="m-0 text-[11px] font-mono font-bold tracking-[0.15em] text-foreground uppercase flex items-center gap-2">
              <span className="text-brass/70">{'//'}</span> Milestones
            </h2>
            <div className="h-[1px] bg-border/40 flex-1 border-dashed border-b border-border/50" />
          </div>
          <MilestoneTracker />
        </section>

        {/* Output Depth (Conditional) */}
        {uploadedFileName && (
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 opacity-80">
              <h2 className="m-0 text-[11px] font-mono font-bold tracking-[0.15em] text-foreground uppercase flex items-center gap-2">
                <span className="text-brass/70">{'//'}</span> Output_Depth
              </h2>
              <div className="h-[1px] bg-border/40 flex-1 border-dashed border-b border-border/50" />
            </div>
            <TierSelector />
          </section>
        )}

        {/* Analytics Charts */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-3 opacity-80">
            <h2 className="m-0 text-[11px] font-mono font-bold tracking-[0.15em] text-foreground uppercase flex items-center gap-2">
              <span className="text-brass/70">{'//'}</span> Analytics
            </h2>
            <div className="h-[1px] bg-border/40 flex-1 border-dashed border-b border-border/50" />
          </div>
          <StatsCharts />
        </section>

        {/* Proposal output content */}
        <ReportView />
      </main>

      {/* Slide-Up Drawers */}
      <LogsDrawer />
      <DocumentsDrawer />
    </div>
  );
};