import { create } from 'zustand';
import { useLogsStore } from './logsStore';

export interface HistoryItem {
  id: string;
  name: string;
  type: 'pdf' | 'docx';
  timestamp: string;
  decompScore: number;
  paramCertainty: number;
  reportContent: string;
}

interface PanelState {
  isPanelOpen: boolean;
  activeMilestoneIndex: number; // -1 means none, 0 to 4
  milestoneStatuses: ('pending' | 'active' | 'completed')[];
  selectedTier: 'brief' | 'detailed' | 'implement';
  uploadedFileName: string | null;
  uploadedFileType: 'pdf' | 'docx' | null;
  isAnalyzing: boolean;
  decompScore: number;
  paramCertainty: number;
  reportContent: string | null;
  isLogsOpen: boolean;
  isHistoryOpen: boolean;
  uploadedHistory: HistoryItem[];

  selectedModel: string;
  setSelectedModel: (model: string) => void;

  togglePanel: () => void;
  setPanelOpen: (isOpen: boolean) => void;
  setSelectedTier: (tier: 'brief' | 'detailed' | 'implement') => void;
  toggleLogs: () => void;
  setLogsOpen: (isOpen: boolean) => void;
  toggleHistory: () => void;
  setHistoryOpen: (isOpen: boolean) => void;
  resetAnalysis: () => void;
  triggerUpload: (filename: string, type: 'pdf' | 'docx') => void;
  loadHistoryItem: (item: HistoryItem) => void;
  deleteHistoryItem: (id: string) => void;
  startAnalysis: (filename: string, type: 'pdf' | 'docx') => void;
  setMilestoneActive: (idx: number) => void;
  completeAnalysis: (reportContent: string) => void;
  failAnalysis: (error: string) => void;
}

export const usePanelStore = create<PanelState>((set, get) => ({
  isPanelOpen: true,
  activeMilestoneIndex: -1,
  milestoneStatuses: Array(5).fill('pending'),
  selectedTier: 'detailed',
  uploadedFileName: null,
  uploadedFileType: null,
  isAnalyzing: false,
  decompScore: 0,
  paramCertainty: 0,
  reportContent: null,
  isLogsOpen: false,
  isHistoryOpen: false,
  uploadedHistory: [],
  selectedModel: 'qwen2.5-coder:1.5b',
  setSelectedModel: (model) => set({ selectedModel: model }),

  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),
  setPanelOpen: (isOpen) => set({ isPanelOpen: isOpen }),
  setSelectedTier: (tier) => set({ selectedTier: tier }),
  toggleLogs: () => set((state) => ({ isLogsOpen: !state.isLogsOpen })),
  setLogsOpen: (isOpen) => set({ isLogsOpen: isOpen }),
  toggleHistory: () => set((state) => ({ isHistoryOpen: !state.isHistoryOpen })),
  setHistoryOpen: (isOpen) => set({ isHistoryOpen: isOpen }),
  
  resetAnalysis: () => set({
    activeMilestoneIndex: -1,
    milestoneStatuses: Array(5).fill('pending'),
    uploadedFileName: null,
    uploadedFileType: null,
    isAnalyzing: false,
    decompScore: 0,
    paramCertainty: 0,
    reportContent: null,
  }),

  loadHistoryItem: (item) => {
    const completedStatuses = Array(5).fill('completed');
    set({
      uploadedFileName: item.name,
      uploadedFileType: item.type,
      activeMilestoneIndex: 4,
      milestoneStatuses: completedStatuses,
      decompScore: item.decompScore,
      paramCertainty: item.paramCertainty,
      reportContent: item.reportContent,
      isHistoryOpen: false,
    });
    const { addLog } = useLogsStore.getState();
    addLog(`[System] Loaded history proposal report for: ${item.name}`, 'system');
  },

  deleteHistoryItem: (id) => {
    set((state) => ({
      uploadedHistory: state.uploadedHistory.filter((item) => item.id !== id),
    }));
  },

  startAnalysis: (filename, type) => {
    const cleanStatuses = Array(5).fill('pending');
    cleanStatuses[0] = 'active';
    set({
      uploadedFileName: filename,
      uploadedFileType: type,
      isAnalyzing: true,
      activeMilestoneIndex: 0,
      milestoneStatuses: cleanStatuses,
      decompScore: 10,
      paramCertainty: 5,
      reportContent: null,
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
      uploadedHistory: [...state.uploadedHistory, historyItem]
    }));
  },

  failAnalysis: (error) => {
    set({
      isAnalyzing: false
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
  }
}));
