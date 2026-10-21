import type { StateCreator } from 'zustand';
import type { PanelState, HistoryItem } from '../panelStore';
import { useLogsStore } from '../logsStore';
import { API_BASE, getPipelineEventsUrl, getPipelineManifestUrl, getPaperUrl } from '../../config/api';
import { getPaperId } from '../utils/storeUtils';
import {
  parseUploadResponse,
  parseJobStart,
  parseExtractionStatus,
  parsePaperReport,
  parseSseError,
  parseV2PipelineEvent,
  parseRunManifest,
  type RunManifest,
} from '../../schemas/api';

/**
 * Exact truth node progress percentages from backend/app/core/events.py
 */
export const NODE_PROGRESS_MAP: Record<string, number> = {
  ingestion_node: 15,
  extraction_node: 30,
  parameter_extraction_node: 30,
  feasibility_node: 45,
  adaptation_node: 50,
  sequencing_node: 60,
  specification_node: 70,
  code_generation_node: 85,
  repair_node: 92,
  code_repair_node: 92,
  evaluation_node: 95,
  completed: 100,
};

/**
 * Backend Node -> Frontend Milestone Index (0-8) mapping for all 9 steps
 */
export const NODE_TO_MILESTONE: Record<string, number> = {
  ingestion_node: 0,
  extraction_node: 1,
  parameter_extraction_node: 1,
  feasibility_node: 2,
  adaptation_node: 3,
  sequencing_node: 4,
  specification_node: 5,
  code_generation_node: 6,
  evaluation_node: 7,
  repair_node: 8,
  code_repair_node: 8,
};

/**
 * Human-readable labels for backend pipeline nodes
 */
export const NODE_LABELS: Record<string, string> = {
  ingestion_node: 'Paper Ingestion',
  extraction_node: 'Method Decomposition',
  parameter_extraction_node: 'Method Decomposition',
  feasibility_node: 'Hardware Feasibility',
  adaptation_node: 'Parameter Adaptation',
  sequencing_node: 'Build Sequencing',
  specification_node: 'Architecture Spec',
  code_generation_node: 'Code Generation',
  evaluation_node: 'Code Verification',
  repair_node: 'Auto-Repair (Reflexion)',
  code_repair_node: 'Auto-Repair (Reflexion)',
  completed: 'Pipeline Complete',
};

/**
 * Node -> Mascot Animation State Mapping (10 V2 States)
 */
export const NODE_MASCOT_MAP: Record<string, string> = {
  ingestion_node: 'reading',
  extraction_node: 'analyzing',
  parameter_extraction_node: 'analyzing',
  feasibility_node: 'evaluating',
  adaptation_node: 'adapting',
  sequencing_node: 'planning',
  specification_node: 'architecting',
  code_generation_node: 'coding',
  evaluation_node: 'testing',
  repair_node: 'debugging',
  code_repair_node: 'debugging',
  completed: 'ready',
};

export interface AnalysisSlice {
  activeMilestoneIndex: number;
  milestoneStatuses: ('pending' | 'active' | 'completed')[];
  pipelineProgress: number; // Real 0–100 % from backend
  currentNode: string | null;
  currentNodeLabel: string | null;
  conditionalMilestonesVisible: Record<string, boolean>;
  uploadedFileName: string | null;
  uploadedFileType: 'pdf' | 'docx' | null;
  isAnalyzing: boolean;
  decompScore: number;
  paramCertainty: number;
  reportContent: string | null;
  analysisStatus: 'idle' | 'analyzing' | 'paused_for_review' | 'success' | 'error';
  manifest: RunManifest | null;

  resetAnalysis: () => void;
  startAnalysis: (filename: string, type: 'pdf' | 'docx', filePath: string | null) => void;
  setMilestoneActive: (idx: number, progress?: number) => void;
  setNodeProgress: (nodeName: string, explicitProgress?: number, isStarting?: boolean) => void;
  setConditionalMilestoneVisible: (nodeKey: string, visible: boolean) => void;
  completeAnalysis: (reportContent: string) => void;
  completeIngestion: () => void;
  failAnalysis: (error: string) => void;
  uploadPaper: (file: File) => Promise<void>;
  generateCode: (customParams?: Record<string, any>) => Promise<void>;
  triggerAnalysis: () => Promise<void>;
  approveParameters: (customParams: Record<string, any>) => Promise<void>;
  fetchManifest: (jobIdOrPaperId: string) => Promise<void>;
  initIpcListeners: () => void;
}

export const createAnalysisSlice: StateCreator<PanelState, [], [], AnalysisSlice> = (set, get) => ({
  activeMilestoneIndex: -1,
  milestoneStatuses: Array(9).fill('pending'),
  pipelineProgress: 0,
  currentNode: null,
  currentNodeLabel: null,
  conditionalMilestonesVisible: {
    adaptation_node: false,
    repair_node: false,
  },
  uploadedFileName: null,
  uploadedFileType: null,
  isAnalyzing: false,
  decompScore: 0,
  paramCertainty: 0,
  reportContent: null,
  analysisStatus: 'idle',
  manifest: null,

  fetchManifest: async (jobIdOrPaperId: string) => {
    if (!jobIdOrPaperId) return;
    try {
      const resp = await fetch(getPipelineManifestUrl(jobIdOrPaperId));
      if (resp.ok) {
        const raw = await resp.json();
        const parsed = parseRunManifest(raw);
        set({ manifest: parsed });
      } else {
        // Fallback to /papers/{paper_id}/manifest
        const altResp = await fetch(`${API_BASE}/papers/${jobIdOrPaperId}/manifest`);
        if (altResp.ok) {
          const raw = await altResp.json();
          const parsed = parseRunManifest(raw);
          set({ manifest: parsed });
        }
      }
    } catch (err) {
      console.warn("[AnalysisSlice] Failed to fetch run manifest:", err);
    }
  },

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
      milestoneStatuses: Array(9).fill('pending'),
      pipelineProgress: 0,
      currentNode: null,
      currentNodeLabel: null,
      conditionalMilestonesVisible: {
        adaptation_node: false,
        repair_node: false,
      },
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
    const cleanStatuses = Array(9).fill('pending');
    cleanStatuses[0] = 'active';
    const paperId = getPaperId(filename);
    set({
      uploadedFileName: filename,
      uploadedFileType: type,
      activePaperPath: filePath,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      pipelineProgress: 15,
      decompScore: 15,
      paramCertainty: 15,
      currentNode: 'ingestion_node',
      currentNodeLabel: 'Paper Ingestion',
      conditionalMilestonesVisible: {
        adaptation_node: false,
        repair_node: false,
      },
      reportContent: null,
      messages: [],
      activeConversationId: null,
      activeConversationTitle: null,
      activePaperId: paperId,
      analysisStatus: 'analyzing'
    });
  },

  setMilestoneActive: (idx, explicitProgress) => {
    const statuses = [...get().milestoneStatuses];
    for (let i = 0; i < idx; i++) {
      statuses[i] = 'completed';
    }
    if (idx < statuses.length) {
      statuses[idx] = 'active';
    }
    const realProg = (typeof explicitProgress === 'number')
      ? Math.min(100, Math.max(0, Math.round(explicitProgress)))
      : (idx >= 0 && idx < 9 ? Math.min(100, Math.round((idx + 1) * 11.1)) : get().pipelineProgress);

    set({
      activeMilestoneIndex: idx,
      milestoneStatuses: statuses,
      pipelineProgress: realProg,
      decompScore: realProg,
      paramCertainty: realProg
    });
  },

  setNodeProgress: (nodeName, explicitProgress, isStarting = true) => {
    const milestoneIdx = NODE_TO_MILESTONE[nodeName];
    const label = NODE_LABELS[nodeName] || nodeName;
    const mappedProg = NODE_PROGRESS_MAP[nodeName] || 0;
    const rawProg = typeof explicitProgress === 'number' ? explicitProgress : mappedProg;
    const progress = Math.min(100, Math.max(0, Math.round(rawProg)));

    const currentStatuses = [...get().milestoneStatuses];
    const conditionalVisible = { ...get().conditionalMilestonesVisible };

    if (nodeName === 'adaptation_node') {
      conditionalVisible.adaptation_node = true;
    }
    if (nodeName === 'repair_node' || nodeName === 'code_repair_node') {
      conditionalVisible.repair_node = true;
    }

    if (typeof milestoneIdx === 'number' && milestoneIdx >= 0 && milestoneIdx < currentStatuses.length) {
      for (let i = 0; i < milestoneIdx; i++) {
        currentStatuses[i] = 'completed';
      }
      if (isStarting) {
        currentStatuses[milestoneIdx] = 'active';
      } else {
        currentStatuses[milestoneIdx] = 'completed';
      }
    }

    set({
      pipelineProgress: progress,
      decompScore: progress,
      paramCertainty: progress,
      currentNode: nodeName,
      currentNodeLabel: label,
      activeMilestoneIndex: typeof milestoneIdx === 'number' ? milestoneIdx : get().activeMilestoneIndex,
      milestoneStatuses: currentStatuses,
      conditionalMilestonesVisible: conditionalVisible,
    });
  },

  setConditionalMilestoneVisible: (nodeKey, visible) => {
    set((state) => ({
      conditionalMilestonesVisible: {
        ...state.conditionalMilestonesVisible,
        [nodeKey]: visible,
      }
    }));
  },

  completeAnalysis: (reportContent) => {
    const completedStatuses = Array(9).fill('completed');
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
        activeMilestoneIndex: 8,
        milestoneStatuses: completedStatuses,
        pipelineProgress: 100,
        decompScore: 100,
        paramCertainty: 100,
        currentNode: 'completed',
        currentNodeLabel: 'Pipeline Complete',
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
      get().fetchManifest(paperId);
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
        activeMilestoneIndex: 8,
        milestoneStatuses: completedStatuses,
        pipelineProgress: 100,
        decompScore: 100,
        paramCertainty: 100,
        currentNode: 'completed',
        currentNodeLabel: 'Pipeline Complete',
        reportContent,
        activeConversationTitle: cleanTitle,
        uploadedHistory: [...state.uploadedHistory, historyItem],
        messages: [],
        analysisStatus: 'success'
      }));
      get().fetchManifest(paperId);
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

    const ingestionStatuses = Array(9).fill('pending');
    ingestionStatuses[0] = 'completed';
    ingestionStatuses[1] = 'active';

    if (existingConvId) {
      if (hasRealTitle) {
        get().updateConversationTitle(existingConvId, paperOrPdfTitle);
      }
      set(() => ({
        isAnalyzing: false,
        activeMilestoneIndex: 1,
        milestoneStatuses: ingestionStatuses,
        pipelineProgress: 30,
        decompScore: 30,
        paramCertainty: 30,
        currentNode: 'extraction_node',
        currentNodeLabel: 'Method Decomposition',
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
          milestoneStatuses: ingestionStatuses,
          pipelineProgress: 30,
          decompScore: 30,
          paramCertainty: 30,
          currentNode: 'extraction_node',
          currentNodeLabel: 'Method Decomposition',
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
      analysisStatus: 'error',
      currentNode: 'failed',
      currentNodeLabel: 'Pipeline Failed',
    });
    const { addLog } = useLogsStore.getState();
    addLog(`[Error] Analysis halted: ${error}`, 'error');
  },

  uploadPaper: async (file: File) => {
    const { addLog } = useLogsStore.getState();
    const filename = file.name;

    const cleanInitialTitle = filename.replace(/\.(pdf|docx)$/i, '');
    const cleanStatuses = Array(9).fill('pending');
    cleanStatuses[0] = 'active';
    set({
      uploadedFileName: filename,
      uploadedFileType: 'pdf',
      activeConversationTitle: cleanInitialTitle,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      pipelineProgress: 15,
      decompScore: 15,
      paramCertainty: 15,
      currentNode: 'ingestion_node',
      currentNodeLabel: 'Paper Ingestion',
      conditionalMilestonesVisible: {
        adaptation_node: false,
        repair_node: false,
      },
      reportContent: null,
      messages: [],
      analysisStatus: 'analyzing'
    });
    addLog(`[System] Uploading: ${filename}`, 'system');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResp = await fetch(`${API_BASE}/papers/upload?model_name=${get().selectedModel}`, {
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

      // Stream pipeline progress via SSE (V2 pipeline events endpoint)
      const eventSource = new EventSource(getPipelineEventsUrl(activeJobId));
      let pipelineCompletedOk = false;

      const handleCompleted = () => {
        if (pipelineCompletedOk) return;
        pipelineCompletedOk = true;
        try { eventSource.close(); } catch {}
        addLog('[Success] Pipeline completed! Ingestion finished.', 'success');
        get().completeIngestion();
        if (typeof window !== 'undefined') {
          if (window.mascotAPI?.setMascotState) {
            window.mascotAPI.setMascotState('excited');
          }
          window.dispatchEvent(new CustomEvent('refresh-model-limits'));
        }
      };

      const handleFailed = (err?: string) => {
        try { eventSource.close(); } catch {}
        const msg = err || 'Pipeline failed';
        get().failAnalysis(msg);
        addLog(`[Error] Pipeline failed: ${msg}`, 'error');
        if (typeof window !== 'undefined' && window.mascotAPI?.setMascotState) {
          window.mascotAPI.setMascotState('sleeping');
        }
      };

      // V2: node_started — fires when any LangGraph pipeline node begins execution
      eventSource.addEventListener('node_started', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, true);

          const label = NODE_LABELS[nodeName] || nodeName;
          const progText = data.progress !== undefined ? ` (${Math.round(data.progress)}%)` : '';
          addLog(`[System] Step started: ${label}${progText}`, 'info');

          // Check mascot state with NODE_MASCOT_MAP fallback
          const mascotState = (data.metadata?.mascot_state as string) || (data as any).mascot_state || NODE_MASCOT_MAP[nodeName];
          if (mascotState && typeof window !== 'undefined' && window.mascotAPI?.setMascotState) {
            window.mascotAPI.setMascotState(mascotState);
          }

          if (nodeName === 'ingestion_node' || nodeName === 'code_generation_node') {
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('refresh-model-limits'));
            }
          }
        } catch (err) {
          console.warn('[SSE] Failed to parse node_started event:', err);
        }
      });

      // V2: node_completed — fires when any LangGraph pipeline node completes successfully
      eventSource.addEventListener('node_completed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, false);

          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Step complete: ${label}`, 'info');

          if (nodeName === 'ingestion_node' || nodeName === 'code_generation_node') {
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('refresh-model-limits'));
            }
          }
        } catch (err) {
          console.warn('[SSE] Failed to parse node_completed event:', err);
        }
      });

      // V2: refinement — parameter adaptation loop feedback
      eventSource.addEventListener('refinement', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const reason = (data.metadata?.reason as string) || 'Adapting parameters for hardware constraints...';
          const attempt = (data.metadata?.attempt as number) || 1;
          get().setConditionalMilestoneVisible('adaptation_node', true);
          get().setNodeProgress('adaptation_node', data.progress || 50, true);

          addLog(`[System] Parameter Refinement (Attempt ${attempt}): ${reason}`, 'info');
          if (typeof window !== 'undefined' && window.mascotAPI?.setMascotState) {
            window.mascotAPI.setMascotState('adapting');
          }
        } catch (err) {
          console.warn('[SSE] Failed to parse refinement event:', err);
        }
      });

      // V2: retry — reflexion auto-repair loop feedback
      eventSource.addEventListener('retry', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const errSummary = (data.metadata?.error_summary as string) || 'Self-repairing code...';
          const attempt = (data.metadata?.attempt as number) || 1;
          const maxRetries = (data.metadata?.max_retries as number) || 3;
          get().setConditionalMilestoneVisible('repair_node', true);
          get().setNodeProgress('repair_node', data.progress || 92, true);

          addLog(`[System] Auto-Repair Reflexion (Attempt ${attempt}/${maxRetries}): ${errSummary}`, 'warning');
          if (typeof window !== 'undefined' && window.mascotAPI?.setMascotState) {
            window.mascotAPI.setMascotState('fixing');
          }
        } catch (err) {
          console.warn('[SSE] Failed to parse retry event:', err);
        }
      });

      // V2: mascot_state / mascot-state — drives mascot animations
      const handleMascotState = (e: MessageEvent) => {
        try {
          let state = '';
          try {
            const parsed = JSON.parse(e.data);
            state = parsed.state || parsed.mascot_state || parsed.metadata?.mascot_state || (typeof parsed === 'string' ? parsed : '');
          } catch {
            state = e.data;
          }
          if (state && typeof window !== 'undefined' && window.mascotAPI?.setMascotState) {
            window.mascotAPI.setMascotState(state);
          }
        } catch {}
      };
      eventSource.addEventListener('mascot_state', handleMascotState);
      eventSource.addEventListener('mascot-state', handleMascotState);

      // V2 & backward-compat: pipeline completion
      eventSource.addEventListener('pipeline_completed', handleCompleted);
      eventSource.addEventListener('COMPLETED', handleCompleted);
      eventSource.addEventListener('completed', handleCompleted);
      eventSource.addEventListener('finished', handleCompleted);

      // V2 & backward-compat: pipeline failure & error
      const handleErrorEvent = (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data || '{}');
          const errMsg = parsed.error || parsed.detail || parsed.metadata?.error || parsed.message || 'Pipeline execution failed';
          handleFailed(errMsg);
        } catch {
          handleFailed(e.data || 'Pipeline execution failed');
        }
      };
      eventSource.addEventListener('pipeline_failed', handleErrorEvent);
      eventSource.addEventListener('ERROR', handleErrorEvent);
      eventSource.addEventListener('error', handleErrorEvent);
      eventSource.addEventListener('failed', handleErrorEvent);

      // Legacy fallback listeners
      eventSource.addEventListener('SECTION_DETECTED', () => get().setMilestoneActive(0, 15));
      eventSource.addEventListener('RAG_READY', () => get().setMilestoneActive(1, 30));
      eventSource.addEventListener('ANALYSIS_STARTED', () => get().setMilestoneActive(2, 45));
      eventSource.addEventListener('CODE_GENERATION_STARTED', () => get().setMilestoneActive(6, 85));
      eventSource.addEventListener('VERIFICATION_STARTED', () => get().setMilestoneActive(7, 95));

      // Handle stream disconnection or completion
      eventSource.onerror = async () => {
        try { eventSource.close(); } catch {}
        if (pipelineCompletedOk) return;

        // Verify if paper was already indexed and stored successfully
        try {
          const checkResp = await fetch(getPaperUrl(effPaperId));
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

    get().setNodeProgress('code_generation_node', 85, true);
    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
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

      const eventSource = new EventSource(getPipelineEventsUrl(job_id));
      let pipelineCompletedOk = false;

      const handleCodeCompleted = async () => {
        if (pipelineCompletedOk) return;
        pipelineCompletedOk = true;
        try { eventSource.close(); } catch {}
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
      };

      const handleCodeFailed = (errMsg?: string) => {
        try { eventSource.close(); } catch {}
        const msg = errMsg || 'Code generation failed';
        get().failAnalysis(msg);
        addLog(`[Error] Code generation failed: ${msg}`, 'error');
      };

      eventSource.addEventListener('node_started', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, true);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Node started: ${label}${data.progress ? ` (${Math.round(data.progress)}%)` : ''}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('node_completed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, false);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Node complete: ${label}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('retry', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const errSummary = (data.metadata?.error_summary as string) || 'Self-repairing code...';
          const attempt = (data.metadata?.attempt as number) || 1;
          const maxRetries = (data.metadata?.max_retries as number) || 3;
          get().setConditionalMilestoneVisible('repair_node', true);
          get().setNodeProgress('repair_node', data.progress || 92, true);
          addLog(`[System] Reflexion Auto-Repair (Attempt ${attempt}/${maxRetries}): ${errSummary}`, 'warning');
        } catch {}
      });

      eventSource.addEventListener('VERIFICATION_STARTED', () => {
        get().setNodeProgress('evaluation_node', 95, true);
        addLog('[System] Code generated. Autonomous 3-layer verification running...', 'info');
      });

      eventSource.addEventListener('pipeline_completed', handleCodeCompleted);
      eventSource.addEventListener('COMPLETED', handleCodeCompleted);
      eventSource.addEventListener('completed', handleCodeCompleted);

      eventSource.addEventListener('pipeline_failed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          handleCodeFailed((data.metadata?.error as string) || data.status || undefined);
        } catch {
          handleCodeFailed(e.data);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        try {
          const data = parseSseError(JSON.parse(e.data || '{}'));
          handleCodeFailed(data.error);
        } catch {
          handleCodeFailed(e.data);
        }
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        try { eventSource.close(); } catch {}
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

    get().setNodeProgress('extraction_node', 30, true);
    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
    });

    try {
      const response = await fetch(`${API_BASE}/pipeline/analyze`, {
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

      const eventSource = new EventSource(getPipelineEventsUrl(job_id));
      let pipelineCompletedOk = false;

      const handleAnalysisCompleted = async () => {
        if (pipelineCompletedOk) return;
        pipelineCompletedOk = true;
        try { eventSource.close(); } catch {}
        addLog('[Success] Analysis completed successfully!', 'success');

        try {
          const statusResp = await fetch(`${API_BASE}/analyze/${job_id}/status`);
          const statusData = parseExtractionStatus(await statusResp.json());
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed.`);
        }
      };

      const handleAnalysisFailed = (errMsg?: string) => {
        try { eventSource.close(); } catch {}
        const msg = errMsg || 'Analysis failed';
        get().failAnalysis(msg);
        addLog(`[Error] Analysis failed: ${msg}`, 'error');
      };

      eventSource.addEventListener('node_started', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, true);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Step started: ${label}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('node_completed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, false);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Step complete: ${label}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('refinement', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const reason = (data.metadata?.reason as string) || 'Optimizing parameters...';
          get().setConditionalMilestoneVisible('adaptation_node', true);
          get().setNodeProgress('adaptation_node', data.progress || 50, true);
          addLog(`[System] Parameter Refinement: ${reason}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('PAUSED_FOR_REVIEW', () => {
        try { eventSource.close(); } catch {}
        set({
          isAnalyzing: false,
          analysisStatus: 'paused_for_review',
        });
        get().setNodeProgress('feasibility_node', 45, false);
        addLog('[System] Pipeline paused for parameter review before code generation.', 'info');
      });

      eventSource.addEventListener('pipeline_completed', handleAnalysisCompleted);
      eventSource.addEventListener('COMPLETED', handleAnalysisCompleted);
      eventSource.addEventListener('completed', handleAnalysisCompleted);

      eventSource.addEventListener('pipeline_failed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          handleAnalysisFailed((data.metadata?.error as string) || data.status || undefined);
        } catch {
          handleAnalysisFailed(e.data);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        try {
          const data = parseSseError(JSON.parse(e.data || '{}'));
          handleAnalysisFailed(data.error);
        } catch {
          handleAnalysisFailed(e.data);
        }
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        try { eventSource.close(); } catch {}
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

    get().setNodeProgress('sequencing_node', 60, true);
    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
    });

    try {
      const response = await fetch(`${API_BASE}/papers/${activePaperId}/approve_parameters?model_name=${selectedModel}`, {
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

      const eventSource = new EventSource(getPipelineEventsUrl(job_id));
      let pipelineCompletedOk = false;

      const handleApprovalCompleted = async () => {
        if (pipelineCompletedOk) return;
        pipelineCompletedOk = true;
        try { eventSource.close(); } catch {}
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
      };

      const handleApprovalFailed = (errMsg?: string) => {
        try { eventSource.close(); } catch {}
        const msg = errMsg || 'Analysis failed';
        get().failAnalysis(msg);
        addLog(`[Error] Analysis failed: ${msg}`, 'error');
      };

      eventSource.addEventListener('node_started', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, true);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Node started: ${label}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('node_completed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          const nodeName = data.node || '';
          get().setNodeProgress(nodeName, data.progress, false);
          const label = NODE_LABELS[nodeName] || nodeName;
          addLog(`[System] Node complete: ${label}`, 'info');
        } catch {}
      });

      eventSource.addEventListener('pipeline_completed', handleApprovalCompleted);
      eventSource.addEventListener('COMPLETED', handleApprovalCompleted);
      eventSource.addEventListener('completed', handleApprovalCompleted);

      eventSource.addEventListener('pipeline_failed', (e: MessageEvent) => {
        try {
          const data = parseV2PipelineEvent(JSON.parse(e.data || '{}'));
          handleApprovalFailed((data.metadata?.error as string) || data.status || undefined);
        } catch {
          handleApprovalFailed(e.data);
        }
      });

      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        try {
          const data = parseSseError(JSON.parse(e.data || '{}'));
          handleApprovalFailed(data.error);
        } catch {
          handleApprovalFailed(e.data);
        }
      });

      // onerror fires on network drop / server crash — do NOT treat as success
      eventSource.onerror = () => {
        try { eventSource.close(); } catch {}
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
          const cleanStatuses = Array(9).fill('pending');
          cleanStatuses[0] = 'active';
          set({
            uploadedFileName: status.filename,
            uploadedFileType: status.type,
            activePaperPath: status.filePath,
            isAnalyzing: true,
            activeMilestoneIndex: 0,
            milestoneStatuses: cleanStatuses,
            pipelineProgress: 15,
            decompScore: 15,
            paramCertainty: 15,
            currentNode: 'ingestion_node',
            currentNodeLabel: 'Paper Ingestion',
            conditionalMilestonesVisible: {
              adaptation_node: false,
              repair_node: false,
            },
            reportContent: null,
            messages: [],
            activeConversationId: null,
            analysisStatus: 'analyzing'
          });
          addLog(`[System] Ingestion pipeline started for: ${status.filename}`, 'system');
        } else {
          set({ isAnalyzing: false, analysisStatus: 'error', currentNode: 'failed', currentNodeLabel: 'Pipeline Failed' });
          addLog(`[Error] Ingestion failed: ${status.error}`, 'error');
        }
      });

      window.mascotAPI.onPipelineLog((log) => {
        const text = log.text;
        addLog(text, 'info');

        // Check for node keywords or legacy step markers
        if (text.includes("ingestion_node") || text.includes("SECTION_DETECTED") || text.includes("Step 1")) {
          get().setNodeProgress("ingestion_node", 15, true);
        } else if (text.includes("extraction_node") || text.includes("RAG_READY") || text.includes("Step 2")) {
          get().setNodeProgress("extraction_node", 30, true);
        } else if (text.includes("feasibility_node") || text.includes("Step 3:")) {
          get().setNodeProgress("feasibility_node", 45, true);
        } else if (text.includes("adaptation_node") || text.includes("Step 3b")) {
          get().setConditionalMilestoneVisible("adaptation_node", true);
          get().setNodeProgress("adaptation_node", 50, true);
        } else if (text.includes("sequencing_node") || text.includes("Step 4:")) {
          get().setNodeProgress("sequencing_node", 60, true);
        } else if (text.includes("specification_node") || text.includes("Step 4b")) {
          get().setNodeProgress("specification_node", 70, true);
        } else if (text.includes("code_generation_node") || text.includes("CODE_GENERATION_STARTED") || text.includes("Step 5")) {
          get().setNodeProgress("code_generation_node", 85, true);
        } else if (text.includes("evaluation_node") || text.includes("VERIFICATION_STARTED") || text.includes("Step 6:")) {
          get().setNodeProgress("evaluation_node", 95, true);
        } else if (text.includes("repair_node") || text.includes("code_repair_node") || text.includes("Step 6b")) {
          get().setConditionalMilestoneVisible("repair_node", true);
          get().setNodeProgress("repair_node", 92, true);
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
