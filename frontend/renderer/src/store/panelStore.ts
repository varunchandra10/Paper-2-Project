import { create } from 'zustand';
import { createUISlice, type UISlice } from './slices/uiSlice';
import { createProfileSlice, type ProfileSlice } from './slices/profileSlice';
import { createChatSlice, type ChatSlice } from './slices/chatSlice';
import { createAnalysisSlice, type AnalysisSlice } from './slices/analysisSlice';

export interface HistoryItem {
  id: string; // Maps to conversation_id
  name: string;
  type: 'pdf' | 'docx';
  timestamp: string;
  decompScore: number;
  paramCertainty: number;
  reportContent: string;
  size?: number;
  uploadedAt?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  attachment?: {
    filename: string;
    paperId: string;
  };
}

export type PanelState = UISlice & ProfileSlice & ChatSlice & AnalysisSlice;

export const usePanelStore = create<PanelState>()((...a) => ({
  ...createUISlice(...a),
  ...createProfileSlice(...a),
  ...createChatSlice(...a),
  ...createAnalysisSlice(...a),
}));
