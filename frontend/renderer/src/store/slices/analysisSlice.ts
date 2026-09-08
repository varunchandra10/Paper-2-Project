import type { StateCreator } from 'zustand';
import type { PanelState, HistoryItem } from '../panelStore';
import { useLogsStore } from '../logsStore';
import { API_BASE } from '../../config/api';
import { getPaperId } from '../utils/storeUtils';
import {
  parseUploadResponse,
  parseJobStart,
  parseExtractionStatus,
  parsePaperReport,
  parseSseError
} from '../../schemas/api';

export interface AnalysisSlice {
  activeMilestoneIndex: number;
  milestoneStatuses: ('pending' | 'active' | 'completed')[];
  uploadedFileName: string | null;
  uploadedFileType: 'pdf' | 'docx' | null;
  isAnalyzing: boolean;
  decompScore: number;
  paramCertainty: number;
  reportContent: string | null;
  analysisStatus: 'idle' | 'analyzing' | 'paused_for_review' | 'success' | 'error';

  resetAnalysis: () => void;
  startAnalysis: (filename: string, type: 'pdf' | 'docx', filePath: string | null) => void;
  setMilestoneActive: (idx: number) => void;
  completeAnalysis: (reportContent: string) => void;
  completeIngestion: () => void;
  failAnalysis: (error: string) => void;
  uploadPaper: (file: File) => Promise<void>;
  generateCode: (customParams?: Record<string, any>) => Promise<void>;
  triggerAnalysis: () => Promise<void>;
  approveParameters: (customParams: Record<string, any>) => Promise<void>;
  initIpcListeners: () => void;
}

export const createAnalysisSlice: StateCreator<PanelState, [], [], AnalysisSlice> = (set, get) => ({
  activeMilestoneIndex: -1,
  milestoneStatuses: Array(5).fill('pending'),
  uploadedFileName: null,
  uploadedFileType: null,
  isAnalyzing: false,
  decompScore: 0,
  paramCertainty: 0,
  reportContent: null,
  analysisStatus: 'idle',

  resetAnalysis: () => {
    try {
      localStorage.removeItem('active_conversation_id');
      localStorage.removeItem('active_conversation_title');
    } catch {}
    fetch(`${API_BASE}/conversations/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: null })
    }).catch(() => {});

    set({
      activeMilestoneIndex: -1,
      milestoneStatuses: Array(5).fill('pending'),
      uploadedFileName: null,
      uploadedFileType: null,
      isAnalyzing: false,
      decompScore: 0,
      paramCertainty: 0,
      reportContent: null,
      messages: [],
      activeConversationId: null,
      activeConversationTitle: null,
      activePaperId: null,
      activePaperPath: null,
      analysisStatus: 'idle'
    });
  },

  startAnalysis: (filename, type, filePath) => {
    const cleanStatuses = Array(5).fill('pending');
    cleanStatuses[0] = 'active';
    const paperId = getPaperId(filename);
    set({
      uploadedFileName: filename,
      uploadedFileType: type,
      activePaperPath: filePath,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      decompScore: 10,
      paramCertainty: 5,
      reportContent: null,
      messages: [],
      activeConversationId: null,
      activeConversationTitle: null,
      activePaperId: paperId,
      analysisStatus: 'analyzing'
    });
  },

  setMilestoneActive: (idx) => {
    const statuses = [...get().milestoneStatuses];
    for (let i = 0; i < idx; i++) {
      statuses[i] = 'completed';
    }
    if (idx < 5) {
      statuses[idx] = 'active';
    }
    const nextDecomp = Math.min(100, 15 + idx * 20);
    const nextCertainty = Math.min(100, 10 + idx * 21);
    set({
      activeMilestoneIndex: idx,
      milestoneStatuses: statuses,
      decompScore: nextDecomp,
      paramCertainty: nextCertainty
    });
  },

  completeAnalysis: (reportContent) => {
    const completedStatuses = Array(5).fill('completed');
    const filename = get().uploadedFileName || "document.pdf";
    const type = get().uploadedFileType || "pdf";
    const paperId = get().activePaperId || getPaperId(filename);
    const cleanTitle = get().uploadedHistory.find(h => h.id === paperId || h.name === filename)?.title || filename.replace(/\.(pdf|docx)$/i, '');

    get().createConversation(cleanTitle, paperId).then((convId) => {
      const historyItem: HistoryItem = {
        id: convId,
        name: filename,
        type,
        timestamp: new Date().toLocaleTimeString(),
        decompScore: 100,
        paramCertainty: 100,
        reportContent,
      };

      try {
        localStorage.setItem('active_conversation_id', convId);
        if (cleanTitle) localStorage.setItem('active_conversation_title', cleanTitle);
      } catch {}
      fetch(`${API_BASE}/conversations/active`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: convId })
      }).catch(() => {});

      set((state) => ({
        isAnalyzing: false,
        activeMilestoneIndex: 4,
        milestoneStatuses: completedStatuses,
        decompScore: 100,
        paramCertainty: 100,
        reportContent,
        activeConversationId: convId,
        activeConversationTitle: cleanTitle,
        activePaperId: paperId,
        uploadedHistory: [...state.uploadedHistory, historyItem],
        messages: [],
        analysisStatus: 'success'
      }));
      get().fetchConversations();
      get().fetchUploadedPapers();
    }).catch((err) => {
      console.error("Failed to create conversation after complete:", err);
      const historyItem: HistoryItem = {
        id: crypto.randomUUID(),
        name: filename,
        type,
        timestamp: new Date().toLocaleTimeString(),
        decompScore: 100,
        paramCertainty: 100,
        reportContent,
      };

      set((state) => ({
        isAnalyzing: false,
        activeMilestoneIndex: 4,
        milestoneStatuses: completedStatuses,
        decompScore: 100,
        paramCertainty: 100,
        reportContent,
        activeConversationTitle: cleanTitle,
        uploadedHistory: [...state.uploadedHistory, historyItem],
        messages: [],
        analysisStatus: 'success'
      }));
    });
  },

  completeIngestion: async () => {
    const filename = get().uploadedFileName || "document.pdf";
    const paperId = get().activePaperId || getPaperId(filename);
    const existingConvId = get().activeConversationId;

    await get().fetchUploadedPapers();
    const foundPaper = get().uploadedHistory.find(h => h.id === paperId || h.name === filename);
    const hasRealTitle = !!(foundPaper?.title && foundPaper.title !== foundPaper.name && !foundPaper.title.toLowerCase().endsWith('.pdf'));
    const paperOrPdfTitle: string = (hasRealTitle && foundPaper?.title) ? foundPaper.title : filename;

    if (existingConvId) {
      if (hasRealTitle) {
        get().updateConversationTitle(existingConvId, paperOrPdfTitle);
      }
      set(() => ({
        isAnalyzing: false,
        activeMilestoneIndex: 1,
        milestoneStatuses: ['completed', 'completed', 'pending', 'pending', 'pending'],
        decompScore: 10,
        paramCertainty: 10,
        reportContent: null,
        activeConversationTitle: paperOrPdfTitle,
        activePaperId: paperId,
        messages: [],
        analysisStatus: 'success'
      }));
      get().fetchConversations();
    } else {
      get().createConversation(paperOrPdfTitle, paperId).then((convId) => {
        set(() => ({
          isAnalyzing: false,
          activeMilestoneIndex: 1,
          milestoneStatuses: ['completed', 'completed', 'pending', 'pending', 'pending'],
          decompScore: 10,
          paramCertainty: 10,
          reportContent: null,
          activeConversationId: convId,
          activeConversationTitle: paperOrPdfTitle,
          activePaperId: paperId,
          messages: [],
          analysisStatus: 'success'
        }));
        get().fetchConversations();
      }).catch((err) => {
        console.warn("Could not create conversation in completeIngestion:", err);
      });
    }
  },

  failAnalysis: (error) => {
    set({
      isAnalyzing: false,
      analysisStatus: 'error'
    });
    const { addLog } = useLogsStore.getState();
    addLog(`[Error] Analysis halted: ${error}`, 'error');
  },

  uploadPaper: async (file: File) => {
    const { addLog } = useLogsStore.getState();
    const filename = file.name;

    const cleanInitialTitle = filename.replace(/\.(pdf|docx)$/i, '');
    const cleanStatuses = Array(5).fill('pending');
    cleanStatuses[0] = 'active';
    set({
      uploadedFileName: filename,
      uploadedFileType: 'pdf',
      activeConversationTitle: cleanInitialTitle,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      decompScore: 10,
      paramCertainty: 5,
      reportContent: null,
      messages: [],
      analysisStatus: 'analyzing'
    });
    addLog(`[System] Uploading: ${filename}`, 'system');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResp = await fetch(`${API_BASE}/history/upload?model_name=${get().selectedModel}`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResp.ok) {
        const errJson = await uploadResp.json().catch(() => ({}));
        throw new Error(errJson.detail || `Upload failed (${uploadResp.status})`);
      }

      const uploadData = parseUploadResponse(await uploadResp.json());
      const { job_id, paper_id, limits, conversation_id } = uploadData;
      const activeJobId = job_id || paper_id || 'active_job';
      addLog(`[System] Upload complete. Pipeline started (job: ${activeJobId})`, 'system');
      const effPaperId = paper_id || activeJobId;
      set({ activePaperId: effPaperId });

      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('refresh-model-limits', { 
          detail: { paper_id: effPaperId, limits } 
        }));
      }

      try {
        const paperTitle = (uploadData.title && uploadData.title !== 'Unknown Title' && !uploadData.title.toLowerCase().endsWith('.pdf'))
          ? uploadData.title
          : cleanInitialTitle;
        const convId = conversation_id || await get().createConversation(paperTitle, effPaperId);

        try {
          if (convId) localStorage.setItem('active_conversation_id', convId);
          localStorage.setItem('active_conversation_title', paperTitle);
        } catch {}

        set({ activeConversationId: convId, activeConversationTitle: paperTitle });
        get().fetchConversations();
      } catch (err) {
        console.warn("Could not sync conversation for paper:", err);
      }

      // Fast-path for duplicate papers: already ingested and indexed, complete immediately
      if (uploadData.duplicate) {
        addLog(`[System] Paper already ingested (${effPaperId}). Reusing existing index.`, 'info');
        get().completeIngestion();
        return;
      }

      // Stream pipeline progress via SSE
      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${activeJobId}`);
      // Track whether COMPLETED fired — distinguishes clean finish from network drop
      let pipelineCompletedOk = false;

      const handleCompleted = () => {
        if (pipelineCompletedOk) return;
        pipelineCompletedOk = true;
        try { eventSource.close(); } catch {}
        addLog('[Success] Pipeline completed! Ingestion finished.', 'success');
        get().completeIngestion();
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('refresh-model-limits'));
        }
      };

      const handleFailed = (err?: string) => {
        try { eventSource.close(); } catch {}
        const msg = err || 'Pipeline failed';
        get().failAnalysis(msg);
        addLog(`[Error] Pipeline failed: ${msg}`, 'error');
      };

      eventSource.addEventListener('SECTION_DETECTED', () => {
        get().setMilestoneActive(0);
        addLog('[System] Step 1: Section detection complete.', 'info');
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('refresh-model-limits'));
        }
      });
      eventSource.addEventListener('RAG_READY', () => {
        get().setMilestoneActive(1);
        addLog('[System] Step 2: RAG vector cache ready.', 'info');
      });
      eventSource.addEventListener('ANALYSIS_STARTED', () => {
        get().setMilestoneActive(2);
        addLog('[System] Step 3: Method decomposition running...', 'info');
      });
      eventSource.addEventListener('CODE_GENERATION_STARTED', () => {
        get().setMilestoneActive(3);
        addLog('[System] Step 4: Code generation started.', 'info');
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('refresh-model-limits'));
        }
      });
      eventSource.addEventListener('VERIFICATION_STARTED', () => {
        get().setMilestoneActive(4);
        addLog('[System] Step 5: Code verification running...', 'info');
      });

      // Bind all completion event variants
      eventSource.addEventListener('COMPLETED', handleCompleted);
      eventSource.addEventListener('completed', handleCompleted);
      eventSource.addEventListener('finished', handleCompleted);

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data || '{}');
          handleFailed(data.error);
        } catch {
          handleFailed(e.data);
        }
      });
      eventSource.addEventListener('failed', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data || '{}');
          handleFailed(data.error);
        } catch {
          handleFailed(e.data);
        }
      });

      // Handle stream disconnection or completion
      eventSource.onerror = async () => {
        try { eventSource.close(); } catch {}
        if (pipelineCompletedOk) return;

        // Verify if paper was already indexed and stored successfully
        try {
          const checkResp = await fetch(`${API_BASE}/history/${effPaperId}`);
          if (checkResp.ok) {
            handleCompleted();
            return;
          }
        } catch {}

        if (get().isAnalyzing) {
          get().failAnalysis('Pipeline connection lost. Please check the server and retry.');
          addLog('[Error] Pipeline SSE connection lost unexpectedly.', 'error');
        }
      };

    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Upload failed: ${err.message}`, 'error');
    }
  },

  generateCode: async (customParams?: Record<string, any>) => {
    const { activePaperId, selectedModel } = get();
    if (!activePaperId) return;

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Code generation requested for paper: ${activePaperId}`, 'system');

    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
      activeMilestoneIndex: 3,
      milestoneStatuses: ['completed', 'completed', 'completed', 'active', 'pending']
    });

    try {
      const response = await fetch(`${API_BASE}/papers/${activePaperId}/synthesize?model_name=${selectedModel}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          custom_parameters: customParams || null
        })
      });

      if (!response.ok) {
        throw new Error(`Code generation failed: ${response.statusText}`);
      }

      const { job_id } = parseJobStart(await response.json());
      addLog(`[System] Code generation job started: ${job_id}`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);
      let pipelineCompletedOk = false;

      eventSource.addEventListener('VERIFICATION_STARTED', () => {
        get().setMilestoneActive(4);
        addLog('[System] Code generated. Autonomous 3-layer verification running...', 'info');
      });

      eventSource.addEventListener('COMPLETED', async () => {
        pipelineCompletedOk = true;
        eventSource.close();
        addLog('[Success] Code generation and verification completed!', 'success');

        try {
          const reportResp = await fetch(`${API_BASE}/papers/${activePaperId}/report`);
          if (reportResp.ok) {
            const reportData = parsePaperReport(await reportResp.json());
            if (reportData.report) {
              get().completeAnalysis(reportData.report);
              return;
            }
          }
          const statusResp = await fetch(`${API_BASE}/analyze/${job_id}/status`);
          const statusData = parseExtractionStatus(await statusResp.json());
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Code synthesized.`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Code synthesized.`);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = parseSseError(JSON.parse(e.data || '{}'));
        get().failAnalysis(data.error || 'Code generation failed');
        addLog(`[Error] Code generation failed: ${data.error}`, 'error');
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        eventSource.close();
        if (!pipelineCompletedOk && get().isAnalyzing) {
          get().failAnalysis('Code generation connection lost. Please check the server and retry.');
          addLog('[Error] Code generation SSE connection lost unexpectedly.', 'error');
        }
      };

    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Code generation request failed: ${err.message}`, 'error');
    }
  },

  triggerAnalysis: async () => {
    const { activePaperId, selectedModel } = get();
    if (!activePaperId) return;

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Analysis requested for: ${activePaperId}`, 'system');

    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
      activeMilestoneIndex: 1,
      milestoneStatuses: ['completed', 'active', 'pending', 'pending', 'pending']
    });

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          paper_id: activePaperId,
          model_name: selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger analysis: ${response.statusText}`);
      }

      const { job_id } = parseJobStart(await response.json());
      addLog(`[System] Analysis pipeline resumed (job: ${job_id})`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);
      let pipelineCompletedOk = false;

      eventSource.addEventListener('PAUSED_FOR_REVIEW', () => {
        eventSource.close();
        set({
          isAnalyzing: false,
          analysisStatus: 'paused_for_review',
          activeMilestoneIndex: 2,
          milestoneStatuses: ['completed', 'completed', 'active', 'pending', 'pending']
        });
        addLog('[System] Pipeline paused for parameter review before code generation.', 'info');
      });

      eventSource.addEventListener('COMPLETED', async () => {
        pipelineCompletedOk = true;
        eventSource.close();
        addLog('[Success] Analysis completed successfully!', 'success');

        try {
          const statusResp = await fetch(`${API_BASE}/analyze/${job_id}/status`);
          const statusData = parseExtractionStatus(await statusResp.json());
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = parseSseError(JSON.parse(e.data || '{}'));
        get().failAnalysis(data.error || 'Analysis failed');
        addLog(`[Error] Analysis failed: ${data.error}`, 'error');
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        eventSource.close();
        if (!pipelineCompletedOk && get().isAnalyzing) {
          get().failAnalysis('Analysis connection lost. Please check the server and retry.');
          addLog('[Error] Analysis SSE connection lost unexpectedly.', 'error');
        }
      };
    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Analysis failed to start: ${err.message}`, 'error');
    }
  },

  approveParameters: async (customParams: Record<string, any>) => {
    const { activePaperId, selectedModel } = get();
    if (!activePaperId) return;

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Submitting approved parameters: ${JSON.stringify(customParams)}`, 'system');

    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
      activeMilestoneIndex: 2,
      milestoneStatuses: ['completed', 'completed', 'active', 'pending', 'pending']
    });

    try {
      const response = await fetch(`${API_BASE}/history/${activePaperId}/approve_parameters?model_name=${selectedModel}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ custom_parameters: customParams })
      });

      if (!response.ok) {
        throw new Error(`Failed to approve parameters (${response.status})`);
      }

      const { job_id } = parseJobStart(await response.json());
      addLog(`[System] Resuming analysis task (job: ${job_id})`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);
      let pipelineCompletedOk = false;

      eventSource.addEventListener('COMPLETED', async () => {
        pipelineCompletedOk = true;
        eventSource.close();
        addLog('[Success] Analysis completed successfully!', 'success');

        try {
          const reportResp = await fetch(`${API_BASE}/papers/${activePaperId}/report`);
          if (reportResp.ok) {
            const reportData = parsePaperReport(await reportResp.json());
            if (reportData.report) {
              get().completeAnalysis(reportData.report);
              return;
            }
          }
          const statusResp = await fetch(`${API_BASE}/analyze/${job_id}/status`);
          const statusData = parseExtractionStatus(await statusResp.json());
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = parseSseError(JSON.parse(e.data || '{}'));
        get().failAnalysis(data.error || 'Analysis failed');
        addLog(`[Error] Analysis failed: ${data.error}`, 'error');
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        eventSource.close();
        if (!pipelineCompletedOk && get().isAnalyzing) {
          get().failAnalysis('Analysis connection lost. Please check the server and retry.');
          addLog('[Error] Analysis SSE connection lost unexpectedly.', 'error');
        }
      };
    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Resuming analysis failed: ${err.message}`, 'error');
    }
  },

  initIpcListeners: () => {
    if (typeof window !== 'undefined' && window.mascotAPI) {
      const { addLog } = useLogsStore.getState();

      window.mascotAPI.onFileStaged((data) => {
        if (data.success) {
          set({
            uploadedFileName: data.filename,
            uploadedFileType: data.type,
            activePaperPath: data.filePath,
          });
          addLog(`[System] File staged: ${data.filename}`, 'system');
        } else {
          addLog(`[Error] Failed to stage file: ${data.error}`, 'error');
        }
      });

      window.mascotAPI.onUploadStatus((status) => {
        if (status.success) {
          const cleanStatuses = Array(5).fill('pending');
          cleanStatuses[0] = 'active';
          set({
            uploadedFileName: status.filename,
            uploadedFileType: status.type,
            activePaperPath: status.filePath,
            isAnalyzing: true,
            activeMilestoneIndex: 0,
            milestoneStatuses: cleanStatuses,
            decompScore: 10,
            paramCertainty: 5,
            reportContent: null,
            messages: [],
            activeConversationId: null,
            analysisStatus: 'analyzing'
          });
          addLog(`[System] Ingestion pipeline started for: ${status.filename}`, 'system');
        } else {
          set({ isAnalyzing: false, analysisStatus: 'error' });
          addLog(`[Error] Ingestion failed: ${status.error}`, 'error');
        }
      });

      window.mascotAPI.onPipelineLog((log) => {
        const text = log.text;
        addLog(text, 'info');

        if (text.includes("SECTION_DETECTED") || text.includes("Step 1")) {
          get().setMilestoneActive(0);
        } else if (text.includes("RAG_READY") || text.includes("Step 2")) {
          get().setMilestoneActive(1);
        } else if (text.includes("ANALYSIS_STARTED") || text.includes("Step 3")) {
          get().setMilestoneActive(2);
        } else if (text.includes("CODE_GENERATION_STARTED") || text.includes("Step 4")) {
          get().setMilestoneActive(3);
        } else if (text.includes("VERIFICATION_STARTED") || text.includes("Step 5")) {
          get().setMilestoneActive(4);
        }
      });

      window.mascotAPI.onPipelineCompleted((status) => {
        if (status.success) {
          addLog(`[Success] Pipeline completed successfully!`, 'success');
          get().completeAnalysis(status.reportContent || '');
        } else {
          get().failAnalysis(status.error || 'Pipeline failed');
          addLog(`[Error] Pipeline failed: ${status.error}`, 'error');
        }
      });
    }
  }
});
