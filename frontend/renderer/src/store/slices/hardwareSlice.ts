import type { StateCreator } from 'zustand';
import type { PanelState } from '../panelStore';
import { API_BASE } from '../../config/api';

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

export interface HardwareSlice {
  hardwareMetrics: HardwareMetrics | null;
  isHardwareLoading: boolean;
  fetchHardwareMetrics: () => Promise<void>;
}

export const createHardwareSlice: StateCreator<PanelState, [], [], HardwareSlice> = (set) => ({
  hardwareMetrics: null,
  isHardwareLoading: false,

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
  }
});
