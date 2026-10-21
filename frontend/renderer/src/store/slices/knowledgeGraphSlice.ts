import type { StateCreator } from 'zustand';
import type { PanelState } from '../panelStore';
import { API_BASE, getPaperKnowledgeGraphUrl } from '../../config/api';

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  node_type: string;
  tier: number;
  color: string;
  badge: string;
  attributes?: Record<string, any>;
}

export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  tier?: number | null;
  tensor_flow?: any;
}

export interface KnowledgeGraphTopologyItem {
  order: number;
  module: string;
  file: string;
  dependencies: string[];
  in_dim?: string;
  out_dim?: string;
}

export interface KnowledgeGraphValidation {
  consistent: boolean;
  dag_acyclic: boolean;
  total_nodes: number;
  total_edges: number;
  parameters_count: number;
  grounded_parameters: number;
  orphaned_parameters: string[];
  ungrounded_count: number;
  warnings: string[];
}

export interface KnowledgeGraphTraceResult {
  found: boolean;
  target: string;
  target_type: string;
  provenance_path: string[];
  grounding_section?: string;
  evidence_quote?: string;
  error?: string;
}

export interface KnowledgeGraphData {
  paper_id: string;
  nodes_count: number;
  edges_count: number;
  hierarchy_levels: number;
  topology: KnowledgeGraphTopologyItem[];
  consistency: KnowledgeGraphValidation;
  visualization: {
    paper_id: string;
    total_nodes: number;
    total_edges: number;
    nodes: KnowledgeGraphNode[];
    edges: KnowledgeGraphEdge[];
    tier_legend: Record<number, { color: string; badge: string; description?: string }>;
  };
  graph?: {
    nodes: any[];
    links: any[];
  };
}

export interface KnowledgeGraphSlice {
  kgData: KnowledgeGraphData | null;
  kgValidation: KnowledgeGraphValidation | null;
  kgTraceResult: KnowledgeGraphTraceResult | null;
  isKgLoading: boolean;
  isKgValidating: boolean;
  isKgTracing: boolean;
  selectedNodeId: string | null;
  highlightedPath: string[];
  visibleTiers: number[];
  showBuildOrder: boolean;
  kgSearchQuery: string;

  fetchKnowledgeGraph: (paperId: string) => Promise<void>;
  validateKg: (paperId: string) => Promise<void>;
  traceEvidence: (paperId: string, entity: string) => Promise<void>;
  setSelectedNodeId: (nodeId: string | null) => void;
  toggleTierVisibility: (tier: number) => void;
  setVisibleTiers: (tiers: number[]) => void;
  setShowBuildOrder: (show: boolean) => void;
  setKgSearchQuery: (query: string) => void;
  clearKgTrace: () => void;
  resetKnowledgeGraph: () => void;
}

export const createKnowledgeGraphSlice: StateCreator<
  PanelState,
  [],
  [],
  KnowledgeGraphSlice
> = (set, get) => ({
  kgData: null,
  kgValidation: null,
  kgTraceResult: null,
  isKgLoading: false,
  isKgValidating: false,
  isKgTracing: false,
  selectedNodeId: null,
  highlightedPath: [],
  visibleTiers: [1, 2, 3, 4, 5, 6, 7],
  showBuildOrder: false,
  kgSearchQuery: '',

  fetchKnowledgeGraph: async (paperId: string) => {
    if (!paperId) return;
    set({ isKgLoading: true });
    try {
      const resp = await fetch(getPaperKnowledgeGraphUrl(paperId));
      if (!resp.ok) {
        throw new Error(`Failed to load knowledge graph: ${resp.statusText}`);
      }
      const data: KnowledgeGraphData = await resp.json();
      set({
        kgData: data,
        kgValidation: data.consistency || null,
        isKgLoading: false
      });
    } catch (err) {
      console.error("[KG Slice] Error fetching knowledge graph:", err);
      set({ isKgLoading: false });
    }
  },

  validateKg: async (paperId: string) => {
    if (!paperId) return;
    set({ isKgValidating: true });
    try {
      const resp = await fetch(`${API_BASE}/papers/${paperId}/knowledge_graph/validate`);
      if (resp.ok) {
        const val: KnowledgeGraphValidation = await resp.json();
        set({ kgValidation: val, isKgValidating: false });
      } else {
        set({ isKgValidating: false });
      }
    } catch (err) {
      console.error("[KG Slice] Error validating knowledge graph:", err);
      set({ isKgValidating: false });
    }
  },

  traceEvidence: async (paperId: string, entity: string) => {
    if (!paperId || !entity) return;
    set({ isKgTracing: true, selectedNodeId: entity });
    try {
      const encodedEntity = encodeURIComponent(entity);
      const resp = await fetch(`${API_BASE}/papers/${paperId}/knowledge_graph/trace/${encodedEntity}`);
      if (resp.ok) {
        const trace: KnowledgeGraphTraceResult = await resp.json();
        set({
          kgTraceResult: trace,
          highlightedPath: trace.provenance_path || [entity],
          isKgTracing: false
        });
      } else {
        set({
          kgTraceResult: null,
          highlightedPath: [entity],
          isKgTracing: false
        });
      }
    } catch (err) {
      console.error("[KG Slice] Error tracing evidence:", err);
      set({
        kgTraceResult: null,
        highlightedPath: [entity],
        isKgTracing: false
      });
    }
  },

  setSelectedNodeId: (nodeId: string | null) => {
    set({ selectedNodeId: nodeId });
  },

  toggleTierVisibility: (tier: number) => {
    const current = get().visibleTiers;
    const exists = current.includes(tier);
    const updated = exists ? current.filter((t) => t !== tier) : [...current, tier].sort();
    set({ visibleTiers: updated });
  },

  setVisibleTiers: (tiers: number[]) => {
    set({ visibleTiers: tiers });
  },

  setShowBuildOrder: (show: boolean) => {
    set({ showBuildOrder: show });
  },

  setKgSearchQuery: (query: string) => {
    set({ kgSearchQuery: query });
  },

  clearKgTrace: () => {
    set({
      kgTraceResult: null,
      highlightedPath: [],
      selectedNodeId: null
    });
  },

  resetKnowledgeGraph: () => {
    set({
      kgData: null,
      kgValidation: null,
      kgTraceResult: null,
      isKgLoading: false,
      isKgValidating: false,
      isKgTracing: false,
      selectedNodeId: null,
      highlightedPath: [],
      visibleTiers: [1, 2, 3, 4, 5, 6, 7],
      showBuildOrder: false,
      kgSearchQuery: ''
    });
  }
});
