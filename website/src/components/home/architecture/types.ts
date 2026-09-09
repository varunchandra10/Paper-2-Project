export type ArchitecturePreset = "e2e" | "langgraph" | "ast_gate";
export type DisplayMode = "graph" | "timeline";

export interface NodeData {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  type: "source" | "process" | "decision" | "storage" | "verify" | "terminal";
  category: string;
  stageNumber?: number;
  stageName?: string;
  name: string;
  subtitle: string;
  file: string;
  icon: string;
  color: string;
  inputs: string[];
  outputs: string[];
  details: string;
  metrics: string;
  tech: string[];
}

export interface EdgeData {
  id: string;
  from: string;
  to: string;
  label?: string;
  style?: "solid" | "dashed" | "loop";
  color?: string;
}

export interface LogEntry {
  time: string;
  nodeId: string;
  text: string;
  status: "info" | "success" | "warning";
}
