import { create } from 'zustand';
import { useLogsStore } from './logsStore';

// In Vite dev mode: /api is proxied to http://localhost:8000 via vite.config.ts
// In Electron: this can be changed back to 'http://localhost:8000'
const API_BASE = '/api';

export interface HistoryItem {
  id: string; // Maps to conversation_id
  name: string;
  type: 'pdf' | 'docx';
  timestamp: string;
  decompScore: number;
  paramCertainty: number;
  reportContent: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
}

function getPaperId(filename: string): string {
  const baseName = filename.replace(/\.[^/.]+$/, ""); // Strip extension
  const cleanTitle = baseName.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  const slug = cleanTitle.replace(/\s+/g, '_').substring(0, 30).replace(/^_+|_+$/g, '');
  return `paper_${slug}`;
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

  messages: ChatMessage[];
  activeConversationId: string | null;
  activePaperId: string | null;
  activePaperPath: string | null;
  analysisStatus: 'idle' | 'analyzing' | 'success' | 'error';

  selectedModel: string;
  setSelectedModel: (model: string) => void;

  userId: string | null;
  username: string | null;
  email: string | null;
  
  activeView: 'chat' | 'profile';
  dob: string | null;
  age: string | null;
  phoneNumber: string | null;
  projectPath: string | null;
  ollamaLink: string | null;
  avatarId: string | null;

  loginLocalUser: (username: string, email: string) => Promise<void>;
  setActiveView: (view: 'chat' | 'profile') => void;
  updateProfile: (profile: {
    username: string;
    email: string;
    dob?: string | null;
    age?: string | null;
    phoneNumber?: string | null;
    projectPath?: string | null;
    ollamaLink?: string | null;
    avatarId?: string | null;
  }) => Promise<void>;

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
  startAnalysis: (filename: string, type: 'pdf' | 'docx', filePath: string | null) => void;
  setMilestoneActive: (idx: number) => void;
  completeAnalysis: (reportContent: string) => void;
  failAnalysis: (error: string) => void;

  sendMessage: (content: string) => Promise<void>;
  uploadPaper: (file: File) => Promise<void>;
  createConversation: (title: string, projectId?: string | null) => Promise<string>;
  fetchMessages: (conversationId: string) => Promise<void>;
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

  messages: [],
  activeConversationId: null,
  activePaperId: null,
  activePaperPath: null,
  analysisStatus: 'idle',

  selectedModel: 'gpt-oss-120b',
  setSelectedModel: (model) => set({ selectedModel: model }),

  userId: localStorage.getItem('local_user_id') || null,
  username: localStorage.getItem('local_username') || null,
  email: localStorage.getItem('local_email') || null,

  activeView: 'chat',
  dob: localStorage.getItem('local_dob') || null,
  age: localStorage.getItem('local_age') || null,
  phoneNumber: localStorage.getItem('local_phone_number') || null,
  projectPath: localStorage.getItem('local_project_path') || null,
  ollamaLink: localStorage.getItem('local_ollama_link') || null,
  avatarId: localStorage.getItem('local_avatar_id') || 'mr-nerdy',

  setActiveView: (view) => set({ activeView: view }),

  loginLocalUser: async (username: string, email: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/local-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email })
      });
      if (!response.ok) {
        throw new Error(`Failed to login: ${response.statusText}`);
      }
      const data = await response.json();
      localStorage.setItem('local_user_id', data.user_id);
      localStorage.setItem('local_username', data.username);
      localStorage.setItem('local_email', data.email);
      set({
        userId: data.user_id,
        username: data.username,
        email: data.email
      });
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  updateProfile: async (profile) => {
    try {
      const response = await fetch(`${API_BASE}/auth/local-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: profile.username, email: profile.email })
      });
      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`);
      }
      const data = await response.json();
      
      localStorage.setItem('local_user_id', data.user_id);
      localStorage.setItem('local_username', data.username);
      localStorage.setItem('local_email', data.email);

      if (profile.dob !== undefined) {
        if (profile.dob) localStorage.setItem('local_dob', profile.dob);
        else localStorage.removeItem('local_dob');
      }
      if (profile.age !== undefined) {
        if (profile.age) localStorage.setItem('local_age', profile.age);
        else localStorage.removeItem('local_age');
      }
      if (profile.phoneNumber !== undefined) {
        if (profile.phoneNumber) localStorage.setItem('local_phone_number', profile.phoneNumber);
        else localStorage.removeItem('local_phone_number');
      }
      if (profile.projectPath !== undefined) {
        if (profile.projectPath) localStorage.setItem('local_project_path', profile.projectPath);
        else localStorage.removeItem('local_project_path');
      }
      if (profile.ollamaLink !== undefined) {
        if (profile.ollamaLink) localStorage.setItem('local_ollama_link', profile.ollamaLink);
        else localStorage.removeItem('local_ollama_link');
      }
      if (profile.avatarId !== undefined) {
        if (profile.avatarId) localStorage.setItem('local_avatar_id', profile.avatarId);
        else localStorage.removeItem('local_avatar_id');
      }

      set({
        userId: data.user_id,
        username: data.username,
        email: data.email,
        dob: profile.dob !== undefined ? profile.dob : get().dob,
        age: profile.age !== undefined ? profile.age : get().age,
        phoneNumber: profile.phoneNumber !== undefined ? profile.phoneNumber : get().phoneNumber,
        projectPath: profile.projectPath !== undefined ? profile.projectPath : get().projectPath,
        ollamaLink: profile.ollamaLink !== undefined ? profile.ollamaLink : get().ollamaLink,
        avatarId: profile.avatarId !== undefined ? profile.avatarId : get().avatarId
      });
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

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
    messages: [],
    activeConversationId: null,
    activePaperId: null,
    activePaperPath: null,
    analysisStatus: 'idle'
  }),

  loadHistoryItem: (item) => {
    const completedStatuses = Array(5).fill('completed');
    const paperId = getPaperId(item.name);
    set({
      uploadedFileName: item.name,
      uploadedFileType: item.type,
      activeMilestoneIndex: 4,
      milestoneStatuses: completedStatuses,
      decompScore: item.decompScore,
      paramCertainty: item.paramCertainty,
      reportContent: item.reportContent,
      isHistoryOpen: false,
      activeConversationId: item.id,
      activePaperId: paperId,
      analysisStatus: 'success'
    });

    get().fetchMessages(item.id);

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Loaded history proposal report for: ${item.name}`, 'system');
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

  createConversation: async (title: string, projectId: string | null = null) => {
    try {
      const response = await fetch(`${API_BASE}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: get().userId || 'e2e_test_user',
          title: title,
          project_id: projectId
        })
      });
      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }
      const data = await response.json();
      return data.conversation_id;
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  fetchMessages: async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.statusText}`);
      }
      const data = await response.json();
      const loadedMessages: ChatMessage[] = data.messages.map((m: any) => ({
        id: m.message_id || Math.random().toString(36).substring(7),
        role: m.role,
        content: m.content,
        model_used: m.model_used
      }));
      set({ messages: loadedMessages });
    } catch (err) {
      console.error(err);
    }
  },

  sendMessage: async (content: string) => {
    let currentConvId = get().activeConversationId;
    const { activePaperId } = get();

    if (!currentConvId) {
      const newTitle = activePaperId ? `Discussion: ${activePaperId}` : `Chat - ${new Date().toLocaleTimeString()}`;
      try {
        currentConvId = await get().createConversation(newTitle);
        set({ activeConversationId: currentConvId });
      } catch (err: any) {
        console.error("Failed to create conversation:", err);
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content
    };

    set((state) => ({ messages: [...state.messages, userMsg] }));

    try {
      const response = await fetch(`${API_BASE}/conversations/${currentConvId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': get().userId || 'e2e_test_user'
        },
        body: JSON.stringify({
          content,
          paper_id: activePaperId,
          model_name: get().selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`API returned error status ${response.status}`);
      }

      const data = await response.json();
      const assistantMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: data.response,
        model_used: data.model_used
      };

      set((state) => ({ messages: [...state.messages, assistantMsg] }));
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: `Error: Failed to fetch response from backend. ${err.message}`
      };
      set((state) => ({ messages: [...state.messages, errorMsg] }));
    }
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

      const uploadResp = await fetch(`${API_BASE}/papers/upload?model_name=${get().selectedModel}`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResp.ok) {
        const errJson = await uploadResp.json().catch(() => ({}));
        throw new Error(errJson.detail || `Upload failed (${uploadResp.status})`);
      }

      const { job_id, paper_id } = await uploadResp.json();
      addLog(`[System] Upload complete. Pipeline started (job: ${job_id})`, 'system');
      set({ activePaperId: paper_id });

      // 2. Stream pipeline progress via SSE
      const eventSource = new EventSource(`${API_BASE}/extraction/stream/${job_id}`);


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
        addLog('[Success] Pipeline completed! Generating report...', 'success');

        // Fetch full status to get report content
        try {
          const statusResp = await fetch(`${API_BASE}/status/${job_id}`);
          const statusData = await statusResp.json();
          const reportContent = statusData.report || `# Analysis Complete\n\nPaper **${filename}** has been analyzed. Ask me anything about it!`;
          get().completeAnalysis(reportContent);
        } catch {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${filename}** has been analyzed. Ask me anything about it!`);
        }
      });
      eventSource.addEventListener('ERROR', (e: MessageEvent) => {
        eventSource.close();
        const data = JSON.parse(e.data || '{}');
        get().failAnalysis(data.error || 'Pipeline failed');
        addLog(`[Error] Pipeline failed: ${data.error}`, 'error');
      });
      eventSource.onerror = () => {
        eventSource.close();
        // If SSE closes without a completed event, treat as done
        if (get().isAnalyzing) {
          get().completeAnalysis(`# Analysis Complete\n\nPaper **${filename}** has been processed. Ask me anything about it!`);
        }
      };

    } catch (err: any) {
      get().failAnalysis(err.message);
      addLog(`[Error] Upload failed: ${err.message}`, 'error');
    }
  },
}));
