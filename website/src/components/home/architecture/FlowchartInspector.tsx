"use client";

import React from "react";
import { NodeData } from "./types";
import { Compass, Code2, ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";

interface FlowchartInspectorProps {
  activeNode: NodeData;
  currentIndex: number;
  totalNodes: number;
  onPrevNode: () => void;
  onNextNode: () => void;
}

export function FlowchartInspector({ 
  activeNode,
  currentIndex,
  totalNodes,
  onPrevNode,
  onNextNode
}: FlowchartInspectorProps) {
  return (
    <div className="p-5 md:p-8 rounded-2xl bg-[#1C1C20] border border-white/10 shadow-2xl backdrop-blur-xl">
      
      {/* Top Header Row with Prev/Next Tour Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-white/8 mb-6">
        
        {/* Category & Status */}
        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span 
              className="text-xs font-mono uppercase tracking-wider font-bold"
              style={{ color: activeNode.color }}
            >
              {activeNode.stageName || activeNode.category}
            </span>
            <span className="text-[#71717A]">•</span>
            <span className="text-xs font-mono text-[#38BDF8] flex items-center gap-1">
              <Compass className="w-3.5 h-3.5" />
              Active Inspection
            </span>
            <span className="text-[#71717A]">•</span>
            <span className="text-xs font-mono text-[#9E9E99]">
              Node {currentIndex + 1} of {totalNodes}
            </span>
          </div>

          <h4 className="text-xl md:text-2xl font-bold font-heading text-[#F4F3EE] flex items-center gap-3 flex-wrap">
            <span>{activeNode.name}</span>
            <span 
              className="text-xs font-mono font-normal px-2.5 py-1 rounded-full border"
              style={{
                backgroundColor: `${activeNode.color}15`,
                borderColor: `${activeNode.color}35`,
                color: activeNode.color,
              }}
            >
              {activeNode.metrics}
            </span>
          </h4>
        </div>

        {/* Tour Navigation Controls (Step Previous / Next) */}
        <div className="flex items-center gap-2 self-stretch sm:self-auto justify-between sm:justify-end">
          <button
            onClick={onPrevNode}
            disabled={currentIndex <= 0}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#18181B] border border-white/10 text-xs font-mono text-[#9E9E99] hover:text-[#F4F3EE] hover:bg-[#222227] disabled:opacity-40 disabled:pointer-events-none transition-all cursor-pointer"
            title="Previous Step"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Prev</span>
          </button>

          <span className="text-xs font-mono text-[#71717A] px-1 sm:hidden">
            {currentIndex + 1} / {totalNodes}
          </span>

          <button
            onClick={onNextNode}
            disabled={currentIndex >= totalNodes - 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#18181B] border border-white/10 text-xs font-mono text-[#9E9E99] hover:text-[#F4F3EE] hover:bg-[#222227] disabled:opacity-40 disabled:pointer-events-none transition-all cursor-pointer"
            title="Next Step"
          >
            <span className="hidden sm:inline">Next</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          {/* Implementation File Path Chip */}
          <div className="hidden lg:flex p-2 rounded-xl bg-[#18181B] border border-white/10 items-center gap-2 font-mono text-xs text-[#38BDF8]">
            <Code2 className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span className="truncate max-w-[220px]">{activeNode.file}</span>
          </div>
        </div>

      </div>

      {/* Description */}
      <p className="text-sm text-[#D4D4D8] leading-relaxed mb-6 font-sans">
        {activeNode.details}
      </p>

      {/* Mobile File Path (shown below description on small screens) */}
      <div className="lg:hidden mb-4 p-2 rounded-xl bg-[#18181B] border border-white/8 flex items-center gap-2 font-mono text-xs text-[#38BDF8]">
        <Code2 className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
        <span className="truncate">{activeNode.file}</span>
      </div>

      {/* Contract Schemas Matrix (Inputs & Outputs) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        
        {/* Input Data Contract */}
        <div className="p-4 rounded-xl bg-[#18181B] border border-white/8 space-y-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#9E9E99] font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#38BDF8]" />
            Input Data Ingestion Contract:
          </span>
          <div className="space-y-1">
            {activeNode.inputs.map((inp, idx) => (
              <div key={idx} className="text-xs font-mono text-[#F4F3EE] flex items-center gap-2">
                <span className="text-[#71717A]">›</span>
                <span>{inp}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Output Artifact Schema */}
        <div className="p-4 rounded-xl bg-[#18181B] border border-white/8 space-y-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#34D399] font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#34D399]" />
            Emitted Artifact Schema / Signals:
          </span>
          <div className="space-y-1">
            {activeNode.outputs.map((out, idx) => (
              <div key={idx} className="text-xs font-mono text-[#34D399] flex items-center gap-2">
                <span className="text-[#34D399]/60">›</span>
                <span>{out}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Underlying Tech Stack Chips */}
      <div className="flex items-center gap-2 pt-4 border-t border-white/8 flex-wrap">
        <span className="text-xs font-mono text-[#71717A] mr-1">
          Internal Engine & Libraries:
        </span>
        {activeNode.tech.map((t) => (
          <span
            key={t}
            className="text-xs font-mono px-3 py-1 rounded-lg bg-[#18181B] border border-white/10 text-[#F4F3EE]"
          >
            {t}
          </span>
        ))}
      </div>

    </div>
  );
}
