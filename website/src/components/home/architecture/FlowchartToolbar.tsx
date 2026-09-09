"use client";

import React from "react";
import { ArchitecturePreset, DisplayMode } from "./types";
import { 
  Play, 
  Pause, 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  Workflow, 
  GitFork, 
  ShieldCheck,
  ListOrdered,
  Network
} from "lucide-react";

interface FlowchartToolbarProps {
  activePreset: ArchitecturePreset;
  onPresetChange: (preset: ArchitecturePreset) => void;
  displayMode: DisplayMode;
  onDisplayModeChange: (mode: DisplayMode) => void;
  isSimulating: boolean;
  onToggleSimulate: () => void;
  zoomScale: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
}

export function FlowchartToolbar({
  activePreset,
  onPresetChange,
  displayMode,
  onDisplayModeChange,
  isSimulating,
  onToggleSimulate,
  zoomScale,
  onZoomIn,
  onZoomOut,
  onResetZoom,
}: FlowchartToolbarProps) {
  return (
    <div className="p-3 md:p-4 rounded-2xl bg-[#1C1C20]/90 border border-white/10 mb-6 backdrop-blur-xl shadow-xl flex flex-col gap-3">
      
      {/* Top Row: Presets & Display Mode Switcher */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        
        {/* Preset Flowchart Mode Buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
          <button
            onClick={() => onPresetChange("e2e")}
            className={`py-1.5 px-3 rounded-xl text-xs font-mono font-semibold transition-all shrink-0 cursor-pointer flex items-center gap-2 ${
              activePreset === "e2e"
                ? "bg-[#DA7756] text-white shadow-[0_0_18px_rgba(218,119,86,0.4)]"
                : "bg-[#222227] border border-white/8 text-[#9E9E99] hover:text-[#F4F3EE]"
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>Master E2E Flow (10 Nodes)</span>
          </button>

          <button
            onClick={() => onPresetChange("langgraph")}
            className={`py-1.5 px-3 rounded-xl text-xs font-mono font-semibold transition-all shrink-0 cursor-pointer flex items-center gap-2 ${
              activePreset === "langgraph"
                ? "bg-[#38BDF8] text-white shadow-[0_0_18px_rgba(56,189,248,0.4)]"
                : "bg-[#222227] border border-white/8 text-[#9E9E99] hover:text-[#F4F3EE]"
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>LangGraph 5-Node Graph</span>
          </button>

          <button
            onClick={() => onPresetChange("ast_gate")}
            className={`py-1.5 px-3 rounded-xl text-xs font-mono font-semibold transition-all shrink-0 cursor-pointer flex items-center gap-2 ${
              activePreset === "ast_gate"
                ? "bg-[#34D399] text-[#18181B] shadow-[0_0_18px_rgba(52,211,153,0.4)] font-bold"
                : "bg-[#222227] border border-white/8 text-[#9E9E99] hover:text-[#F4F3EE]"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Dual Code & AST Gate</span>
          </button>
        </div>

        {/* View Mode Toggle: Graph vs Linear Steps */}
        <div className="flex items-center self-end lg:self-center bg-[#18181B] p-1 rounded-xl border border-white/8 shrink-0">
          <button
            onClick={() => onDisplayModeChange("graph")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              displayMode === "graph"
                ? "bg-[#2A2A32] text-[#F4F3EE] font-bold shadow-sm"
                : "text-[#9E9E99] hover:text-[#F4F3EE]"
            }`}
            title="Interactive Graph Canvas"
          >
            <Network className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>Graph Canvas</span>
          </button>

          <button
            onClick={() => onDisplayModeChange("timeline")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
              displayMode === "timeline"
                ? "bg-[#2A2A32] text-[#F4F3EE] font-bold shadow-sm"
                : "text-[#9E9E99] hover:text-[#F4F3EE]"
            }`}
            title="Step-by-Step Flowchart List"
          >
            <ListOrdered className="w-3.5 h-3.5 text-[#DA7756]" />
            <span>Step Timeline</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Simulation Play/Pause + Zoom Controls */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5 gap-2">
        <div className="flex items-center gap-2">
          {/* Play/Pause Trace Simulation */}
          <button
            onClick={onToggleSimulate}
            className={`flex items-center gap-2 py-1.5 px-3.5 rounded-xl text-xs font-heading font-bold transition-all shadow-md cursor-pointer ${
              isSimulating
                ? "bg-[#EF4444] text-white shadow-[0_0_20px_rgba(239,68,68,0.5)] animate-pulse"
                : "bg-[#DA7756] text-white hover:bg-[#DA7756]/90 shadow-[0_0_18px_rgba(218,119,86,0.35)]"
            }`}
          >
            {isSimulating ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause Trace</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Simulate Signal Trace</span>
              </>
            )}
          </button>

          <span className="text-[11px] font-mono text-[#71717A] hidden sm:inline">
            Interactive pipeline signal animation
          </span>
        </div>

        {/* Zoom Controls (Active in Graph View) */}
        {displayMode === "graph" && (
          <div className="flex items-center bg-[#222227] rounded-xl border border-white/8 p-1">
            <button
              onClick={onZoomOut}
              className="p-1.5 text-[#9E9E99] hover:text-[#F4F3EE] transition-colors cursor-pointer"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[10px] font-mono px-2 text-[#71717A]">
              {Math.round(zoomScale * 100)}%
            </span>
            <button
              onClick={onZoomIn}
              className="p-1.5 text-[#9E9E99] hover:text-[#F4F3EE] transition-colors cursor-pointer"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onResetZoom}
              className="p-1.5 text-[#9E9E99] hover:text-[#F4F3EE] transition-colors border-l border-white/5 ml-1 cursor-pointer"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
