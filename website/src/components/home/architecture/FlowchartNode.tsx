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
  Check 
} from "lucide-react";

interface FlowchartNodeProps {
  node: NodeData;
  isSelected: boolean;
  isHovered: boolean;
  isSimActive: boolean;
  isSimDone: boolean;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

export function FlowchartNode({
  node,
  isSelected,
  isHovered,
  isSimActive,
  isSimDone,
  onSelect,
  onHover,
}: FlowchartNodeProps) {
  const getNodeIcon = (icon: string) => {
    switch (icon) {
      case "file": return <FileText className="w-3.5 h-3.5" />;
      case "layers": return <Layers className="w-3.5 h-3.5" />;
      case "database": return <Database className="w-3.5 h-3.5" />;
      case "workflow": return <Workflow className="w-3.5 h-3.5" />;
      case "cpu": return <Cpu className="w-3.5 h-3.5" />;
      case "shield": return <ShieldCheck className="w-3.5 h-3.5" />;
      case "code": return <Code2 className="w-3.5 h-3.5" />;
      case "monitor": return <Monitor className="w-3.5 h-3.5" />;
      case "sparkles": return <Sparkles className="w-3.5 h-3.5" />;
      case "check": return <CheckCircle2 className="w-3.5 h-3.5" />;
      default: return <Activity className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div
      onClick={() => onSelect(node.id)}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        left: `${node.x}px`,
        top: `${node.y}px`,
        width: `${node.w}px`,
        height: `${node.h}px`,
      }}
      className={`absolute rounded-xl transition-all duration-200 cursor-pointer flex flex-col justify-between p-3.5 z-20 ${
        isSimActive
          ? "bg-[#222227] border-[#DA7756] shadow-[0_0_30px_rgba(218,119,86,0.6)] ring-2 ring-[#DA7756] scale-[1.04]"
          : isSelected
          ? "bg-[#222227] border-[#38BDF8] shadow-[0_0_24px_rgba(56,189,248,0.4)] ring-1.5 ring-[#38BDF8] scale-[1.02]"
          : isHovered
          ? "bg-[#222227]/95 border-white/30 shadow-lg scale-[1.01]"
          : "bg-[#1E1E24]/90 border-white/10 hover:border-white/20"
      } border backdrop-blur-md`}
    >
      {/* Left Input Port Pin */}
      <span 
        className={`absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 transition-all ${
          isSelected || isSimActive
            ? "bg-[#38BDF8] border-white shadow-[0_0_10px_#38BDF8]"
            : "bg-[#18181B] border-white/30"
        }`}
        title="Input Port"
      />

      {/* Right Output Port Pin */}
      <span 
        className={`absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 transition-all ${
          isSelected || isSimActive
            ? "bg-[#DA7756] border-white shadow-[0_0_10px_#DA7756]"
            : "bg-[#18181B] border-white/30"
        }`}
        title="Output Port"
      />

      {/* Top Bar: Category Pill & Status Dot */}
      <div className="flex items-center justify-between">
        <span 
          className="text-[9px] font-mono uppercase tracking-wider font-bold"
          style={{ color: node.color }}
        >
          {node.category}
        </span>

        <div className="flex items-center gap-1.5">
          {isSimActive ? (
            <span className="w-2 h-2 rounded-full bg-[#DA7756] animate-ping" />
          ) : isSimDone ? (
            <Check className="w-3 h-3 text-[#34D399]" />
          ) : (
            <span 
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: node.color }}
            />
          )}
        </div>
      </div>

      {/* Center Content: Icon & Title */}
      <div className="flex items-start gap-2.5 my-1">
        <div 
          className="p-1.5 rounded-lg border flex items-center justify-center shrink-0 mt-0.5"
          style={{
            backgroundColor: `${node.color}15`,
            borderColor: `${node.color}35`,
            color: node.color,
          }}
        >
          {getNodeIcon(node.icon)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="text-xs font-bold font-heading text-[#F4F3EE] truncate leading-tight">
            {node.name}
          </div>
          <div className="text-[10px] font-mono text-[#9E9E99] truncate mt-0.5">
            {node.subtitle}
          </div>
        </div>
      </div>

      {/* Bottom Metric Chip */}
      <div className="pt-1.5 border-t border-white/5 flex items-center justify-between text-[9px] font-mono">
        <span className="text-[#71717A] truncate">
          {node.file.split("/").pop()}
        </span>
        <span 
          className="font-semibold px-1.5 py-0.5 rounded"
          style={{ 
            backgroundColor: `${node.color}18`, 
            color: node.color 
          }}
        >
          {node.metrics}
        </span>
      </div>
    </div>
  );
}
