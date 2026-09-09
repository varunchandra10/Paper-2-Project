"use client";

import React from "react";
import { NodeData } from "./types";
import { 
  FileText, 
  Database, 
  Cpu, 
  ShieldCheck, 
  Monitor, 
  CheckCircle2, 
  Code2, 
  Workflow, 
  Layers, 
  Sparkles, 
  Activity,
  Check,
  ArrowDown
} from "lucide-react";

interface FlowchartTimelineProps {
  nodes: NodeData[];
  selectedNodeId: string;
  activeStepIndex: number;
  onSelectNode: (id: string) => void;
}

export function FlowchartTimeline({
  nodes,
  selectedNodeId,
  activeStepIndex,
  onSelectNode,
}: FlowchartTimelineProps) {
  const getNodeIcon = (icon: string) => {
    switch (icon) {
      case "file": return <FileText className="w-4 h-4" />;
      case "layers": return <Layers className="w-4 h-4" />;
      case "database": return <Database className="w-4 h-4" />;
      case "workflow": return <Workflow className="w-4 h-4" />;
      case "cpu": return <Cpu className="w-4 h-4" />;
      case "shield": return <ShieldCheck className="w-4 h-4" />;
      case "code": return <Code2 className="w-4 h-4" />;
      case "monitor": return <Monitor className="w-4 h-4" />;
      case "sparkles": return <Sparkles className="w-4 h-4" />;
      case "check": return <CheckCircle2 className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="rounded-2xl bg-[#18181B] border border-white/10 p-4 md:p-8 mb-6 shadow-2xl">
      <div className="flex items-center justify-between pb-4 mb-6 border-b border-white/8">
        <div>
          <h4 className="text-sm font-bold font-heading text-[#F4F3EE] uppercase tracking-wider">
            Sequential Pipeline Steps
          </h4>
          <p className="text-xs text-[#9E9E99] font-mono mt-0.5">
            Step-by-step linear flow through all architecture gates
          </p>
        </div>
        <span className="text-xs font-mono text-[#DA7756] bg-[#DA7756]/10 px-2.5 py-1 rounded-full border border-[#DA7756]/20">
          {nodes.length} Verified Milestones
        </span>
      </div>

      <div className="space-y-4 relative before:absolute before:left-5 md:before:left-6 before:top-4 before:bottom-4 before:w-0.5 before:bg-gradient-to-b before:from-[#DA7756] before:via-[#38BDF8] before:to-[#34D399]">
        {nodes.map((node, index) => {
          const isSelected = selectedNodeId === node.id;
          const isSimActive = activeStepIndex === index;
          const isSimDone = activeStepIndex > index;

          return (
            <div
              key={node.id}
              onClick={() => onSelectNode(node.id)}
              className={`relative pl-12 md:pl-16 p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                isSimActive
                  ? "bg-[#222227] border-[#DA7756] shadow-[0_0_24px_rgba(218,119,86,0.4)] scale-[1.01]"
                  : isSelected
                  ? "bg-[#222227] border-[#38BDF8] shadow-[0_0_20px_rgba(56,189,248,0.3)]"
                  : "bg-[#1C1C20]/80 border-white/8 hover:bg-[#222227]/90 hover:border-white/20"
              }`}
            >
              {/* Timeline Connector Indicator Ball */}
              <div
                className={`absolute left-3 md:left-4 top-4.5 -translate-x-1/2 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                  isSimActive
                    ? "bg-[#DA7756] border-white shadow-[0_0_12px_#DA7756]"
                    : isSelected
                    ? "bg-[#38BDF8] border-white shadow-[0_0_10px_#38BDF8]"
                    : isSimDone
                    ? "bg-[#34D399] border-white/50"
                    : "bg-[#18181B] border-white/30"
                }`}
              >
                {isSimDone ? (
                  <Check className="w-3 h-3 text-[#18181B]" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </div>

              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className="text-[10px] font-mono uppercase tracking-wider font-bold px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: `${node.color}15`,
                      color: node.color,
                    }}
                  >
                    {node.stageName || node.category}
                  </span>
                  <span className="text-[10px] font-mono text-[#71717A]">
                    Step 0{index + 1}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-[#71717A] bg-[#18181B] px-2 py-0.5 rounded border border-white/5">
                    {node.file.split("/").pop()}
                  </span>
                  <span
                    className="text-[10px] font-mono font-bold px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: `${node.color}18`,
                      color: node.color,
                    }}
                  >
                    {node.metrics}
                  </span>
                </div>
              </div>

              {/* Title & Description */}
              <div className="flex items-start gap-3">
                <div
                  className="p-2 rounded-lg border shrink-0 mt-0.5"
                  style={{
                    backgroundColor: `${node.color}15`,
                    borderColor: `${node.color}35`,
                    color: node.color,
                  }}
                >
                  {getNodeIcon(node.icon)}
                </div>
                <div className="flex-1 min-w-0">
                  <h5 className="text-sm md:text-base font-bold font-heading text-[#F4F3EE] flex items-center gap-2">
                    <span>{node.name}</span>
                    <span className="text-xs font-mono font-normal text-[#9E9E99]">
                      ({node.subtitle})
                    </span>
                  </h5>
                  <p className="text-xs text-[#D4D4D8] mt-1 leading-relaxed">
                    {node.details}
                  </p>
                </div>
              </div>

              {/* Data Contracts summary */}
              <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="text-[#9E9E99] truncate">
                  <span className="text-[#71717A]">Inputs: </span>
                  <span className="text-[#F4F3EE]">{node.inputs[0]}</span>
                </div>
                <div className="text-[#34D399] truncate sm:text-right">
                  <span className="text-[#71717A]">Emits: </span>
                  <span>{node.outputs[0]}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
