import { create } from 'zustand';

export interface LogLine {
  id: string;
  text: string;
  type: 'system' | 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
}

interface LogsState {
  logs: LogLine[];
  filter: 'all' | 'info' | 'warning' | 'error';
  searchQuery: string;
  addLog: (text: string, type?: LogLine['type']) => void;
  clearLogs: () => void;
  setFilter: (filter: LogsState['filter']) => void;
  setSearchQuery: (query: string) => void;
}

export const useLogsStore = create<LogsState>((set) => ({
  logs: [
    {
      id: 'init',
      text: 'Standing by. Drop a PDF or Word document to begin execution.',
      type: 'system',
      timestamp: new Date().toLocaleTimeString(),
    },
  ],
  filter: 'all',
  searchQuery: '',
  addLog: (text, type = 'info') => {
    set((state) => ({
      logs: [
        ...state.logs,
        {
          id: Math.random().toString(36).substring(7),
          text,
          type,
          timestamp: new Date().toLocaleTimeString(),
        },
      ],
    }));
  },
  clearLogs: () => set({ logs: [] }),
  setFilter: (filter) => set({ filter }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
}));
