import type { StateCreator } from 'zustand';
import type { PanelState, HistoryItem } from '../panelStore';
import { useLogsStore } from '../logsStore';
import { API_BASE } from '../../config/api';
import { getPaperId } from '../utils/storeUtils';

export interface DocumentHistorySlice {
  uploadedHistory: HistoryItem[];
  activePaperId: string | null;
  activePaperPath: string | null;
  isPapersLoading: boolean;

  setActivePaperId: (paperId: string | null) => void;
  fetchUploadedPapers: () => Promise<void>;
  loadHistoryItem: (item: HistoryItem) => Promise<void>;
  deleteHistoryItem: (id: string) => void;
  deleteMultipleHistoryItems: (ids: string[]) => void;
}

export const createDocumentHistorySlice: StateCreator<PanelState, [], [], DocumentHistorySlice> = (set, get) => ({
  uploadedHistory: [],
  activePaperId: null,
  activePaperPath: null,
  isPapersLoading: false,

  setActivePaperId: (paperId) => set({ activePaperId: paperId }),

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
          title: p.title || p.filename,
          authors: Array.isArray(p.authors) ? p.authors : (p.authors ? [p.authors] : []),
          pageCount: p.page_count,
          type: (p.filename || '').endsWith('.docx') ? 'docx' : 'pdf',
          size: p.file_size || 1024 * 1024,
          uploadedAt: p.updated_at ? new Date(p.updated_at * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Today',
          timestamp: p.updated_at ? new Date(p.updated_at * 1000).toLocaleDateString() : 'Today',
          rawDate: p.updated_at ? new Date(p.updated_at * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Today',
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

    const matchingConv = get().conversations.find(c => c.project_id === paperId || c.conversation_id === item.id || c.id === item.id);
    const targetConvId = (matchingConv ? (matchingConv.conversation_id || matchingConv.id) : item.id) || '';
    const resolvedTitle = matchingConv?.title || item.title || item.name;

    try {
      localStorage.setItem('active_conversation_id', targetConvId);
      if (resolvedTitle) {
        localStorage.setItem('active_conversation_title', resolvedTitle);
      }
    } catch {}
    fetch(`${API_BASE}/conversations/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: targetConvId })
    }).catch(() => {});

    set({
      uploadedFileName: item.name,
      uploadedFileType: item.type as 'pdf' | 'docx',
      activeMilestoneIndex: 4,
      milestoneStatuses: completedStatuses,
      decompScore: item.decompScore,
      paramCertainty: item.paramCertainty,
      reportContent: reportContent,
      isHistoryOpen: false,
      activeConversationId: targetConvId,
      activeConversationTitle: resolvedTitle,
      activePaperId: paperId,
      analysisStatus: 'success'
    });

    get().fetchMessages(targetConvId);

    const { addLog } = useLogsStore.getState();
    addLog(`[System] Loaded live proposal report for: ${item.name}`, 'system');
  },

  deleteHistoryItem: (id) => {
    fetch(`${API_BASE}/papers/${id}`, { method: 'DELETE' }).catch(() => {});
    set((state) => ({
      uploadedHistory: state.uploadedHistory.filter((item) => item.id !== id),
    }));
  },

  deleteMultipleHistoryItems: (ids) => {
    ids.forEach((id) => {
      fetch(`${API_BASE}/papers/${id}`, { method: 'DELETE' }).catch(() => {});
    });
    set((state) => ({
      uploadedHistory: state.uploadedHistory.filter((item) => !ids.includes(item.id)),
    }));
  }
});
