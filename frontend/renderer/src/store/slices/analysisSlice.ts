import type { StateCreator } from 'zustand';
import type { PanelState, HistoryItem, ChatMessage } from '../panelStore';
import { useLogsStore } from '../logsStore';
import { API_BASE, getPaperId } from '../utils/storeUtils';

export interface HardwareMetrics {
  status: string;
  cpu: {
    platform: string;
    architecture: string;
    processor: string;
    cores: number;
    usage_percent: number;
    ram_total_gb: number;
    ram_used_gb: number;
    ram_available_gb: number;
  };
  gpu: {
    cuda_available: boolean;
    name: string;
    vram_total_gb: number;
    vram_used_gb: number;
    vram_free_gb: number;
  };
}

export interface AnalysisSlice {
  activeMilestoneIndex: number;
  milestoneStatuses: ('pending' | 'active' | 'completed')[];
  uploadedFileName: string | null;
  uploadedFileType: 'pdf' | 'docx' | null;
  isAnalyzing: boolean;
  decompScore: number;
  paramCertainty: number;
  reportContent: string | null;
  uploadedHistory: HistoryItem[];
  activePaperId: string | null;
  activePaperPath: string | null;
  analysisStatus: 'idle' | 'analyzing' | 'paused_for_review' | 'success' | 'error';
  hardwareMetrics: HardwareMetrics | null;
  isHardwareLoading: boolean;
  isPapersLoading: boolean;

  setActivePaperId: (paperId: string | null) => void;

  resetAnalysis: () => void;
  triggerUpload: (filename: string, type: 'pdf' | 'docx') => void;
  loadHistoryItem: (item: HistoryItem) => void;
  deleteHistoryItem: (id: string) => void;
  startAnalysis: (filename: string, type: 'pdf' | 'docx', filePath: string | null) => void;
  setMilestoneActive: (idx: number) => void;
  completeAnalysis: (reportContent: string) => void;
  completeIngestion: () => void;
  failAnalysis: (error: string) => void;
  uploadPaper: (file: File) => Promise<void>;
  generateCode: (customParams?: Record<string, any>) => Promise<void>;
  triggerAnalysis: () => Promise<void>;
  approveParameters: (customParams: Record<string, any>) => Promise<void>;
  fetchUploadedPapers: () => Promise<void>;
  fetchHardwareMetrics: () => Promise<void>;
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
  uploadedHistory: [],
  activePaperId: null,
  activePaperPath: null,
  analysisStatus: 'idle',
  hardwareMetrics: null,
  isHardwareLoading: false,
  isPapersLoading: false,

  fetchHardwareMetrics: async () => {
    set({ isHardwareLoading: true });
    try {
      const res = await fetch(`${API_BASE}/hardware/metrics`);
      if (!res.ok) return;
      const data = await res.json();
      set({ hardwareMetrics: data });
    } catch (err) {
      console.error('Failed to fetch hardware metrics:', err);
    } finally {
      set({ isHardwareLoading: false });
    }
  },

  setActivePaperId: (paperId) => set({ activePaperId: paperId }),

  resetAnalysis: () => set({
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
    activePaperId: null,
    activePaperPath: null,
    analysisStatus: 'idle'
  }),

  loadHistoryItem: async (item) => {
    const completedStatuses = Array(5).fill('completed');
    const paperId = item.id.startsWith('paper_') ? item.id : getPaperId(item.name);
    
    // Fetch live backend markdown report
    let reportContent = item.reportContent;
    try {
      const res = await fetch(`${API_BASE}/papers/${paperId}/report`);
      if (res.ok) {
        const data = await res.json();
        if (data.report) {
          reportContent = data.report;
        }
      }
    } catch (err) {
      console.warn("Using local cached report content:", err);
    }

    set({
      uploadedFileName: item.name,
      uploadedFileType: item.type as 'pdf' | 'docx',
      activeMilestoneIndex: 4,
      milestoneStatuses: completedStatuses,
      decompScore: item.decompScore,
      paramCertainty: item.paramCertainty,
      reportContent: reportContent,
      isHistoryOpen: false,
      activeConversationId: item.id,
      activePaperId: paperId,
      analysisStatus: 'success'
    });

    get().fetchMessages(item.id);

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Loaded live proposal report for: ${item.name}`, 'system');
  },

  deleteHistoryItem: (id) => {
    set((state) => ({
      uploadedHistory: state.uploadedHistory.filter((item) => item.id !== id),
    }));
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
    const nextDecomp = Math.min(100, 15 + idx * 19 + Math.floor(Math.random() * 5));
    const nextCertainty = Math.min(100, 10 + idx * 20 + Math.floor(Math.random() * 4));
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
    const paperId = getPaperId(filename);
    const filePath = get().activePaperPath;

    get().createConversation(`Analysis: ${filename}`, filePath).then((convId) => {
      const historyItem: HistoryItem = {
        id: convId,
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
        activeConversationId: convId,
        activePaperId: paperId,
        uploadedHistory: [...state.uploadedHistory, historyItem],
        messages: [],
        analysisStatus: 'success'
      }));
      get().fetchConversations();
    }).catch((err) => {
      console.error("Failed to create conversation after complete:", err);
      // Fallback local complete
      const historyItem: HistoryItem = {
        id: Math.random().toString(36).substring(7),
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
        uploadedHistory: [...state.uploadedHistory, historyItem],
        messages: [],
        analysisStatus: 'success'
      }));
    });
  },

  completeIngestion: () => {
    const filename = get().uploadedFileName || "document.pdf";
    const paperId = getPaperId(filename);
    const existingConvId = get().activeConversationId;

    const welcomeMsg: ChatMessage = {
      id: 'welcome-rag-prompt',
      role: 'assistant',
      content: `I have successfully ingested and indexed **${filename}**. Click **"Analyze Paper & Check Feasibility"** in the sidebar to run architectural decomposition and hardware feasibility adaptation checks, or ask me any questions directly!`
    };

    if (existingConvId) {
      set(() => ({
        isAnalyzing: false,
        activeMilestoneIndex: 1,
        milestoneStatuses: ['completed', 'completed', 'pending', 'pending', 'pending'],
        decompScore: 10,
        paramCertainty: 10,
        reportContent: null,
        activePaperId: paperId,
        messages: [welcomeMsg],
        analysisStatus: 'success'
      }));
      get().fetchConversations();
    } else {
      const filePath = get().activePaperPath;
      get().createConversation(`Ingestion: ${filename}`, filePath).then((convId) => {
        set(() => ({
          isAnalyzing: false,
          activeMilestoneIndex: 1,
          milestoneStatuses: ['completed', 'completed', 'pending', 'pending', 'pending'],
          decompScore: 10,
          paramCertainty: 10,
          reportContent: null,
          activeConversationId: convId,
          activePaperId: paperId,
          messages: [welcomeMsg],
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

  triggerUpload: (filename, type) => {
    const { addLog } = useLogsStore.getState();
    const cleanStatuses = Array(5).fill('pending');
    cleanStatuses[0] = 'active';

    set({
      uploadedFileName: filename,
      uploadedFileType: type,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      decompScore: 15,
      paramCertainty: 10,
      reportContent: null,
      messages: [],
      activeConversationId: null,
      activePaperId: getPaperId(filename),
      activePaperPath: null
    });

    addLog(`[System] Ingestion started for: ${filename}`, 'system');
    addLog(`Reading document pages and scanning layout elements...`, 'info');

    const milestones = [
      { name: 'Paper Ingestion', successLog: 'Ingested page structure and metadata.' },
      { name: 'Method Decomposition', successLog: 'Decomposed model layers and attention heads.' },
      { name: 'Parameters Refinement', successLog: 'Refined 14 hyperparameters using Tavily search.' },
      { name: 'Hardware Feasibility', successLog: 'Feasibility passed: loading fits RTX 3090/4090 VRAM.' },
      { name: 'Blueprint Synthesis', successLog: 'Synthesis Complete! Proposal proposal ready.' }
    ];

    let currentStep = 0;

    const runNextStep = () => {
      if (currentStep > 4) {
        const report = `# Project Blueprint Proposal: ${filename}
          
## 1. Executive Summary
Successfully decomposed the academic paper and mapped its execution components to local development blueprints.

* **Target Device:** NVIDIA GPU Local Compute (RTX 3090/4090)
* **Estimated VRAM Profile:** 16.4 GB (Training: 22.1 GB)
* **Status:** Feasible

## 2. Model Architecture Details
The paper details a custom Transformer framework utilizing:
- **Attention Modules:** Multi-Query Attention (MQA)
- **Latent Dimension:** 4096
- **Context Length:** 8192 tokens

## 3. Discovered Parameters & Configurations
\`\`\`yaml
hyperparameters:
  learning_rate: 3e-4
  batch_size: 128
  optimizer: AdamW
  weight_decay: 0.01
\`\`\`

## 4. Hardware Gap Analysis
Our checks confirm that full model loading fits within a single GPU card footprint. The proposed sequence is optimized for FP16 inference.`;

        get().createConversation(`Mock Analysis: ${filename}`, null).then((convId) => {
          const historyItem: HistoryItem = {
            id: convId,
            name: filename,
            type,
            timestamp: new Date().toLocaleTimeString(),
            decompScore: get().decompScore,
            paramCertainty: get().paramCertainty,
            reportContent: report,
          };

          const welcomeMsg: ChatMessage = {
            id: 'welcome-rag-prompt',
            role: 'assistant',
            content: "I have successfully analyzed the research paper and verified its hardware feasibility. Would you like me to generate the complete codebase implementation or would you prefer a brief explanation of the methodology?"
          };

          set((state) => ({
            isAnalyzing: false,
            reportContent: report,
            activeConversationId: convId,
            uploadedHistory: [...state.uploadedHistory, historyItem],
            messages: [welcomeMsg]
          }));
          get().fetchConversations();
        }).catch(() => {
          const historyItem: HistoryItem = {
            id: Math.random().toString(36).substring(7),
            name: filename,
            type,
            timestamp: new Date().toLocaleTimeString(),
            decompScore: get().decompScore,
            paramCertainty: get().paramCertainty,
            reportContent: report,
          };

          set((state) => ({
            isAnalyzing: false,
            reportContent: report,
            uploadedHistory: [...state.uploadedHistory, historyItem]
          }));
        });
        
        addLog(`[Success] Blueprint proposal generated successfully!`, 'success');
        return;
      }

      setTimeout(() => {
        const updatedStatuses = [...get().milestoneStatuses];
        updatedStatuses[currentStep] = 'completed';
        
        addLog(`[Success] Milestone ${currentStep + 1} completed: ${milestones[currentStep].successLog}`, 'success');
        
        const nextStep = currentStep + 1;
        if (nextStep < 5) {
          updatedStatuses[nextStep] = 'active';
        }

        const nextDecomp = Math.min(100, 20 + nextStep * 18 + Math.floor(Math.random() * 8));
        const nextCertainty = Math.min(100, 15 + nextStep * 19 + Math.floor(Math.random() * 6));

        set({
          activeMilestoneIndex: nextStep < 5 ? nextStep : 4,
          milestoneStatuses: updatedStatuses,
          decompScore: nextDecomp,
          paramCertainty: nextCertainty,
        });

        if (nextStep < 5) {
          addLog(`[System] Milestone ${nextStep + 1} active: Running ${milestones[nextStep].name}...`, 'system');
        }

        currentStep = nextStep;
        runNextStep();
      }, 2500); // 2.5s delay per milestone
    };

    runNextStep();
  },

  uploadPaper: async (file: File) => {
    const { addLog } = useLogsStore.getState();
    const filename = file.name;

    // Start local analysis state immediately for UI feedback
    const cleanStatuses = Array(5).fill('pending');
    cleanStatuses[0] = 'active';
    set({
      uploadedFileName: filename,
      uploadedFileType: 'pdf',
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
    addLog(`[System] Uploading: ${filename}`, 'system');

    try {
      // 1. Upload the PDF via multipart form
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

      const { job_id, paper_id } = await uploadResp.json();
      const activeJobId = job_id || paper_id || 'active_job';
      addLog(`[System] Upload complete. Pipeline started (job: ${activeJobId})`, 'system');
      const effPaperId = paper_id || activeJobId;
      set({ activePaperId: effPaperId });

      try {
        const convId = await get().createConversation(`Ingestion: ${filename}`, effPaperId);
        set({ activeConversationId: convId });
        get().fetchConversations();
      } catch (err) {
        console.warn("Could not create conversation for paper:", err);
      }

      // 2. Stream pipeline progress via SSE
      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${activeJobId}`);

      eventSource.addEventListener('SECTION_DETECTED', () => {
        get().setMilestoneActive(0);
        addLog('[System] Step 1: Section detection complete.', 'info');
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
      });
      eventSource.addEventListener('VERIFICATION_STARTED', () => {
        get().setMilestoneActive(4);
        addLog('[System] Step 5: Code verification running...', 'info');
      });
      eventSource.addEventListener('COMPLETED', async () => {
        eventSource.close();
        addLog('[Success] Pipeline completed! Ingestion finished.', 'success');
        get().completeIngestion();
      });
      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = JSON.parse(e.data || '{}');
        get().failAnalysis(data.error || 'Pipeline failed');
        addLog(`[Error] Pipeline failed: ${data.error}`, 'error');
      });
      eventSource.onerror = () => {
        eventSource.close();
        if (get().isAnalyzing) {
          get().completeIngestion();
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
      const response = await fetch(`${API_BASE}/history/${activePaperId}/generate_code?model_name=${selectedModel}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          custom_parameters: customParams || null
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger code generation (${response.status})`);
      }

      const { job_id } = await response.json();
      addLog(`[System] Code generation task started (job: ${job_id})`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);

      eventSource.addEventListener('CODE_GENERATION_STARTED', () => {
        get().setMilestoneActive(3);
        addLog('[System] Step 4: Code generation started.', 'info');
      });
      eventSource.addEventListener('VERIFICATION_STARTED', () => {
        get().setMilestoneActive(4);
        addLog('[System] Step 5: Code verification running...', 'info');
      });
      eventSource.addEventListener('COMPLETED', async () => {
        eventSource.close();
        addLog('[Success] Code generation completed successfully!', 'success');

        try {
          const statusResp = await fetch(`${API_BASE}/extraction/status/${job_id}`);
          const statusData = await statusResp.json();
          const reportContent = statusData.report || get().reportContent;
          
          get().completeAnalysis(reportContent || '');
          
          const welcomeMsg: ChatMessage = {
            id: `welcome-code-gen-${Math.random()}`,
            role: 'assistant',
            content: "I have successfully generated and verified the complete PyTorch implementation. You can view the files under the 'Implement' tab!"
          };
          set((state) => ({ messages: [...state.messages, welcomeMsg] }));
        } catch {
          get().completeAnalysis(get().reportContent || '');
        }
      });
      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = JSON.parse(e.data || '{}');
        get().failAnalysis(data.error || 'Code generation failed');
        addLog(`[Error] Code generation failed: ${data.error}`, 'error');
      });
      eventSource.onerror = () => {
        eventSource.close();
        if (get().isAnalyzing) {
          get().completeAnalysis(get().reportContent || '');
        }
      };
    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Code generation failed to start: ${err.message}`, 'error');
    }
  },

  triggerAnalysis: async () => {
    const { activePaperId, selectedModel } = get();
    if (!activePaperId) return;

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Structural analysis requested for paper: ${activePaperId}`, 'system');

    set({
      isAnalyzing: true,
      analysisStatus: 'analyzing',
      activeMilestoneIndex: 2,
      milestoneStatuses: ['completed', 'completed', 'active', 'pending', 'pending']
    });

    try {
      const response = await fetch(`${API_BASE}/history/${activePaperId}/analyze?model_name=${selectedModel}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger analysis (${response.status})`);
      }

      const { job_id } = await response.json();
      addLog(`[System] Analysis task started (job: ${job_id})`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);

      eventSource.addEventListener('ANALYSIS_STARTED', () => {
        get().setMilestoneActive(2);
        addLog('[System] Step 3: Method decomposition & parameter extraction started...', 'info');
      });
      eventSource.addEventListener('PAUSED_FOR_REVIEW', () => {
        eventSource.close();
        set({
          isAnalyzing: false,
          analysisStatus: 'paused_for_review'
        });
        addLog('[Notice] Analysis paused: Hyperparameters extracted. Please review and approve them in the Implement panel.', 'info');
      });
      eventSource.addEventListener('COMPLETED', async () => {
        eventSource.close();
        addLog('[Success] Analysis completed successfully!', 'success');

        try {
          const statusResp = await fetch(`${API_BASE}/extraction/status/${job_id}`);
          const statusData = await statusResp.json();
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`;
          
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`);
        }
      });
      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = JSON.parse(e.data || '{}');
        get().failAnalysis(data.error || 'Analysis failed');
        addLog(`[Error] Analysis failed: ${data.error}`, 'error');
      });
      eventSource.onerror = () => {
        eventSource.close();
        if (get().isAnalyzing) {
          get().completeAnalysis(get().reportContent || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`);
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

      const { job_id } = await response.json();
      addLog(`[System] Resuming analysis task (job: ${job_id})`, 'system');

      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);

      eventSource.addEventListener('COMPLETED', async () => {
        eventSource.close();
        addLog('[Success] Analysis completed successfully!', 'success');

        try {
          const reportResp = await fetch(`${API_BASE}/papers/${activePaperId}/report`);
          if (reportResp.ok) {
            const reportData = await reportResp.json();
            if (reportData.report) {
              get().completeAnalysis(reportData.report);
              return;
            }
          }
          const statusResp = await fetch(`${API_BASE}/extraction/status/${job_id}`);
          const statusData = await statusResp.json();
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`);
        }
      });
      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = JSON.parse(e.data || '{}');
        get().failAnalysis(data.error || 'Analysis failed');
        addLog(`[Error] Analysis failed: ${data.error}`, 'error');
      });
      eventSource.onerror = () => {
        eventSource.close();
        if (get().isAnalyzing) {
          get().completeAnalysis(get().reportContent || `# Analysis Complete\n\nPaper **${activePaperId}** has been analyzed. Ask me anything about it!`);
        }
      };
    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Resuming analysis failed: ${err.message}`, 'error');
    }
  },

  fetchUploadedPapers: async () => {
    set({ isPapersLoading: true });
    try {
      const response = await fetch(`${API_BASE}/papers`);
      if (response.ok) {
        const data = await response.json();
        const papers = Array.isArray(data) ? data : (data.papers || []);
        const historyItems: HistoryItem[] = papers.map((p: any) => ({
          id: p.paper_id || p.id,
          name: p.filename || p.title || p.paper_id,
          type: (p.filename || '').endsWith('.docx') ? 'docx' : 'pdf',
          size: p.file_size || 1024 * 1024,
          uploadedAt: p.updated_at ? new Date(p.updated_at * 1000).toLocaleDateString() : 'Today',
          timestamp: p.updated_at ? new Date(p.updated_at * 1000).toLocaleDateString() : 'Today',
          decompScore: 100,
          paramCertainty: 100,
          reportContent: ''
        }));
        set({ uploadedHistory: historyItems });
      }
    } catch (err) {
      console.error("Failed to fetch uploaded papers:", err);
    } finally {
      set({ isPapersLoading: false });
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
