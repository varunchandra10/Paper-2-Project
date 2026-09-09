"use client";

import React, { useRef, useState, useEffect } from "react";
import { NodeData, EdgeData, ArchitecturePreset } from "./types";
import { FlowchartNode } from "./FlowchartNode";
import { MoveRight } from "lucide-react";

interface FlowchartCanvasProps {
  activePreset: ArchitecturePreset;
  nodes: NodeData[];
  edges: EdgeData[];
  selectedNodeId: string;
  hoveredNodeId: string | null;
  activeStepIndex: number;
  isSimulating: boolean;
  zoomScale: number;
  onSelectNode: (id: string) => void;
  onHoverNode: (id: string | null) => void;
}

export function FlowchartCanvas({
  activePreset,
  nodes,
  edges,
  selectedNodeId,
  hoveredNodeId,
  activeStepIndex,
  isSimulating,
  zoomScale,
  onSelectNode,
  onHoverNode,
}: FlowchartCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasScrolled, setHasScrolled] = useState(false);

  // SVG Bezier path calculator connecting output port of nodeA to input port of nodeB
  const calculatePath = (edge: EdgeData) => {
    const fromNode = nodes.find((n) => n.id === edge.from);
    const toNode = nodes.find((n) => n.id === edge.to);
    if (!fromNode || !toNode) return "";

    const startX = fromNode.x + fromNode.w;
    const startY = fromNode.y + fromNode.h / 2;
    const endX = toNode.x;
    const endY = toNode.y + toNode.h / 2;

    // Backward retry loop for LangGraph
    if (edge.style === "dashed" && startX > endX) {
      const topArc = Math.min(fromNode.y, toNode.y) - 80;
      return `M ${startX} ${startY} C ${startX + 60} ${topArc}, ${endX - 60} ${topArc}, ${endX} ${endY}`;
    }

    const deltaX = Math.abs(endX - startX) * 0.55;
    return `M ${startX} ${startY} C ${startX + deltaX} ${startY}, ${endX - deltaX} ${endY}, ${endX} ${endY}`;
  };

  // Calculate midpoint for edge labels
  const getEdgeMidpoint = (edge: EdgeData) => {
    const fromNode = nodes.find((n) => n.id === edge.from);
    const toNode = nodes.find((n) => n.id === edge.to);
    if (!fromNode || !toNode) return { x: 0, y: 0 };

    const startX = fromNode.x + fromNode.w;
    const startY = fromNode.y + fromNode.h / 2;
    const endX = toNode.x;
    const endY = toNode.y + toNode.h / 2;

    if (edge.style === "dashed" && startX > endX) {
      return {
        x: (startX + endX) / 2,
        y: Math.min(fromNode.y, toNode.y) - 60,
      };
    }

    return {
      x: (startX + endX) / 2,
      y: (startY + endY) / 2,
    };
  };

  const canvasWidth = 
    activePreset === "e2e" ? 1580 : activePreset === "langgraph" ? 1240 : 1320;

  // Track scroll on mobile to hide hint
  const handleScroll = () => {
    if (!hasScrolled) setHasScrolled(true);
  };

  // Stage columns visual metadata
  const stageColumns = activePreset === "e2e" ? [
    { label: "STAGE 01: MULTI-MODAL INGESTION", x: 20, w: 630, color: "#DA7756" },
    { label: "STAGE 02: MEMORY & GRAPH", x: 660, w: 215, color: "#38BDF8" },
    { label: "STAGE 03: REASONING MESH", x: 885, w: 220, color: "#A855F7" },
    { label: "STAGE 04: SYNTHESIS & AST GATE", x: 1115, w: 215, color: "#34D399" },
    { label: "STAGE 05: DESKTOP & MASCOT", x: 1340, w: 200, color: "#EC4899" },
  ] : activePreset === "langgraph" ? [
    { label: "NODE 1: INGESTION", x: 30, w: 230, color: "#DA7756" },
    { label: "NODE 2: EXTRACTION", x: 270, w: 230, color: "#38BDF8" },
    { label: "NODE 3: FEASIBILITY", x: 510, w: 230, color: "#A855F7" },
    { label: "NODE 4: SEQUENCING", x: 750, w: 230, color: "#34D399" },
    { label: "NODE 5: VERIFICATION", x: 990, w: 230, color: "#EC4899" },
  ] : [
    { label: "01 MILESTONE DAG", x: 30, w: 240, color: "#DA7756" },
    { label: "02 DUAL SYNTHESIS", x: 300, w: 250, color: "#38BDF8" },
    { label: "03 AST SYNTAX", x: 580, w: 220, color: "#34D399" },
    { label: "04 SECURITY AUDIT", x: 820, w: 220, color: "#34D399" },
    { label: "05 TENSOR SIMULATION", x: 1060, w: 230, color: "#34D399" },
  ];

  return (
    <div 
      ref={containerRef}
      onScroll={handleScroll}
      className="rounded-2xl bg-[#18181B] border border-white/10 shadow-2xl relative overflow-x-auto overflow-y-hidden mb-6 select-none"
      style={{ height: "510px" }}
    >
      {/* Mobile Swipe Hint Banner */}
      {!hasScrolled && (
        <div className="md:hidden absolute top-3 right-3 z-30 bg-[#DA7756]/90 text-white text-[10px] font-mono px-2.5 py-1 rounded-full shadow-lg flex items-center gap-1.5 animate-pulse pointer-events-none">
          <span>Swipe to pan</span>
          <MoveRight className="w-3 h-3" />
        </div>
      )}

      {/* Blueprint Dot Grid Texture */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: "radial-gradient(rgba(255, 255, 255, 0.25) 1px, transparent 1px)",
          backgroundSize: "24px 24px"
        }}
      />

      {/* Interactive Graph Canvas Wrapper (with Zoom Transform) */}
      <div 
        className="relative transition-transform duration-200 origin-top-left"
        style={{ 
          width: `${canvasWidth}px`,
          height: "510px",
          transform: `scale(${zoomScale})`
        }}
      >
        {/* Stage Columns Background Bands & Headers */}
        {stageColumns.map((col, idx) => (
          <div
            key={idx}
            style={{
              left: `${col.x}px`,
              top: "14px",
              width: `${col.w}px`,
              height: "480px",
            }}
            className="absolute rounded-xl border border-white/5 bg-white/[0.015] pointer-events-none flex flex-col justify-start p-2.5 z-0"
          >
            <div className="flex items-center gap-2 border-b border-white/5 pb-1.5">
              <span 
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: col.color }}
              />
              <span 
                className="text-[9px] font-mono font-bold tracking-wider uppercase truncate"
                style={{ color: col.color }}
              >
                {col.label}
              </span>
            </div>
          </div>
        ))}

        {/* SVG CONNECTION WIRE LAYER */}
        <svg 
          className="absolute inset-0 w-full h-full pointer-events-none z-10"
          style={{ overflow: "visible" }}
        >
          <defs>
            <marker
              id="arrow-default"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#71717A" />
            </marker>

            <marker
              id="arrow-active"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#DA7756" />
            </marker>

            <marker
              id="arrow-cyan"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#38BDF8" />
            </marker>

            <marker
              id="arrow-emerald"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#34D399" />
            </marker>

            <marker
              id="arrow-red"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#EF4444" />
            </marker>
          </defs>

          {/* Render each connecting wire / edge */}
          {edges.map((edge) => {
            const isHovered = hoveredNodeId === edge.from || hoveredNodeId === edge.to;
            const isSelected = selectedNodeId === edge.from || selectedNodeId === edge.to;
            const pathD = calculatePath(edge);
            const mid = getEdgeMidpoint(edge);

            const strokeColor = 
              isSelected || isHovered 
                ? edge.color || "#DA7756" 
                : "#3F3F46";

            const markerId = 
              edge.color === "#38BDF8" 
                ? "url(#arrow-cyan)" 
                : edge.color === "#34D399" 
                ? "url(#arrow-emerald)"
                : edge.color === "#EF4444"
                ? "url(#arrow-red)"
                : isSelected || isHovered 
                ? "url(#arrow-active)" 
                : "url(#arrow-default)";

            return (
              <g key={edge.id} className="transition-all duration-300">
                {/* Background base path */}
                <path
                  d={pathD}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isSelected || isHovered ? 2.5 : 1.5}
                  strokeDasharray={edge.style === "dashed" ? "5 5" : undefined}
                  markerEnd={markerId}
                  opacity={isSelected || isHovered ? 1 : 0.45}
                />

                {/* Animated moving pulse packets along the path */}
                {(isSelected || isSimulating) && (
                  <path
                    d={pathD}
                    fill="none"
                    stroke={edge.color || "#38BDF8"}
                    strokeWidth={2.5}
                    strokeDasharray="8 14"
                    className="animate-[dash_1.5s_linear_infinite]"
                    opacity={0.8}
                  />
                )}

                {/* Edge Label Badge */}
                {edge.label && (
                  <g transform={`translate(${mid.x}, ${mid.y})`}>
                    <rect
                      x={-edge.label.length * 3.4}
                      y={-10}
                      width={edge.label.length * 6.8}
                      height={18}
                      rx={9}
                      fill="#18181B"
                      stroke={isSelected ? strokeColor : "#27272A"}
                      strokeWidth={1}
                    />
                    <text
                      textAnchor="middle"
                      y={3}
                      fontSize="9"
                      fontFamily="monospace"
                      fill={isSelected ? "#F4F3EE" : "#A1A1AA"}
                    >
                      {edge.label}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>

        {/* FLOWCHART GRAPH NODES LAYER */}
        {nodes.map((node, nodeIdx) => (
          <FlowchartNode
            key={node.id}
            node={node}
            isSelected={selectedNodeId === node.id}
            isHovered={hoveredNodeId === node.id}
            isSimActive={activeStepIndex === nodeIdx}
            isSimDone={activeStepIndex > nodeIdx}
            onSelect={onSelectNode}
            onHover={onHoverNode}
          />
        ))}
      </div>

      {/* Canvas Floating Legend Badge */}
      <div className="absolute bottom-3 left-3 bg-[#1C1C20]/90 border border-white/10 rounded-xl px-3 py-1.5 text-[10px] font-mono text-[#9E9E99] flex items-center gap-3 backdrop-blur-md z-30 pointer-events-none">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-[#38BDF8]" />
          <span>Input Port</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-[#DA7756]" />
          <span>Output Port</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-[#34D399]" />
          <span>Data Stream</span>
        </span>
      </div>
    </div>
  );
}
