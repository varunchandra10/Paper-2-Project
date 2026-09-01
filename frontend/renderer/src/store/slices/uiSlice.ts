import type { StateCreator } from 'zustand';
import type { PanelState } from '../panelStore';

export interface UISlice {
  isPanelOpen: boolean;
  selectedTier: 'brief' | 'detailed' | 'implement';
  isLogsOpen: boolean;
  isHistoryOpen: boolean;
  activeView: 'chat' | 'profile' | 'pdf-viewer';
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  setActiveView: (view: 'chat' | 'profile' | 'pdf-viewer') => void;
  togglePanel: () => void;
  setPanelOpen: (isOpen: boolean) => void;
  setSelectedTier: (tier: 'brief' | 'detailed' | 'implement') => void;
  toggleLogs: () => void;
  setLogsOpen: (isOpen: boolean) => void;
  toggleHistory: () => void;
  setHistoryOpen: (isOpen: boolean) => void;
}

export const createUISlice: StateCreator<PanelState, [], [], UISlice> = (set) => ({
  isPanelOpen: true,
  selectedTier: 'detailed',
  isLogsOpen: false,
  isHistoryOpen: false,
  activeView: 'chat',
  selectedModel: 'llama-3.3-70b',
  setSelectedModel: (model) => set({ selectedModel: model }),
  setActiveView: (view) => set({ activeView: view }),
  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),
  setPanelOpen: (isOpen) => set({ isPanelOpen: isOpen }),
  setSelectedTier: (tier) => set({ selectedTier: tier }),
  toggleLogs: () => set((state) => ({ isLogsOpen: !state.isLogsOpen })),
  setLogsOpen: (isOpen) => set({ isLogsOpen: isOpen }),
  toggleHistory: () => set((state) => ({ isHistoryOpen: !state.isHistoryOpen })),
  setHistoryOpen: (isOpen) => set({ isHistoryOpen: isOpen }),
});
