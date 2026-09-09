"use client";

import React, { useState, useEffect } from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { 
  ArchitecturePreset, 
  DisplayMode,
  LogEntry,
  e2eNodes, 
  e2eEdges, 
  langgraphNodes, 
  langgraphEdges, 
  astGateNodes, 
  astGateEdges,
  FlowchartToolbar,
  FlowchartCanvas,
  FlowchartTimeline,
  FlowchartSimulationTerminal,
  FlowchartInspector
} from "./architecture";

export function ArchitectureSection() {
  const [activePreset, setActivePreset] = useState<ArchitecturePreset>("e2e");
  const [displayMode, setDisplayMode] = useState<DisplayMode>("graph");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("canonical-gate");
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [zoomScale, setZoomScale] = useState<number>(1);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(-1);
  const [simLogs, setSimLogs] = useState<LogEntry[]>([]);

  // Active dataset based on selected preset
  const currentNodes = 
    activePreset === "e2e" 
      ? e2eNodes 
      : activePreset === "langgraph" 
      ? langgraphNodes 
      : astGateNodes;

  const currentEdges = 
    activePreset === "e2e" 
      ? e2eEdges 
      : activePreset === "langgraph" 
      ? langgraphEdges 
      : astGateEdges;

  // Selected node object and current index
  const activeNodeIndex = Math.max(0, currentNodes.findIndex((n) => n.id === selectedNodeId));
  const activeNode = currentNodes[activeNodeIndex] || currentNodes[0];

  // Switch preset helper
  const handlePresetChange = (preset: ArchitecturePreset) => {
    setActivePreset(preset);
    setIsSimulating(false);
    setActiveStepIndex(-1);
    setSimLogs([]);
    if (preset === "e2e") setSelectedNodeId("canonical-gate");
    if (preset === "langgraph") setSelectedNodeId("lg-1");
    if (preset === "ast_gate") setSelectedNodeId("ag-ast1");
  };

  // Next / Previous node navigation
  const handleNextNode = () => {
    if (activeNodeIndex < currentNodes.length - 1) {
      setSelectedNodeId(currentNodes[activeNodeIndex + 1].id);
    }
  };

  const handlePrevNode = () => {
    if (activeNodeIndex > 0) {
      setSelectedNodeId(currentNodes[activeNodeIndex - 1].id);
    }
  };

  // Trace Simulation loop
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isSimulating) {
      const path = currentNodes.map((n) => n.id);
      let step = 0;
      setActiveStepIndex(0);
      setSelectedNodeId(path[0]);
      setSimLogs([
        {
          time: "0.00s",
          nodeId: path[0],
          text: `Pipeline initialized trace at ${currentNodes[0].name}`,
          status: "info",
        }
      ]);

      timer = setInterval(() => {
        step++;
        if (step >= path.length) {
          setIsSimulating(false);
          setActiveStepIndex(path.length - 1);
          setSimLogs((prev) => [
            ...prev,
            {
              time: `${(step * 0.42).toFixed(2)}s`,
              nodeId: path[path.length - 1],
              text: `Pipeline execution trace completed with 100% verification score!`,
              status: "success",
            }
          ]);
          if (timer) clearInterval(timer);
        } else {
          const currentNode = currentNodes[step];
          setActiveStepIndex(step);
          setSelectedNodeId(currentNode.id);
          setSimLogs((prev) => [
            ...prev,
            {
              time: `${(step * 0.42).toFixed(2)}s`,
              nodeId: currentNode.id,
              text: `Dispatched -> ${currentNode.name} (${currentNode.metrics})`,
              status: "info",
            }
          ]);
        }
      }, 1300);
    } else {
      setActiveStepIndex(-1);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isSimulating, activePreset]);

  return (
    <section id="architecture" className="py-20 md:py-28 bg-[#141416] border-t border-white/8 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/3 -translate-x-1/2 w-[700px] h-[350px] bg-[#DA7756]/10 rounded-full blur-[160px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-[600px] h-[350px] bg-[#38BDF8]/8 rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading */}
        <SectionHeading
          badge="INTERACTIVE FLOW CHART & GRAPH"
          badgeVariant="accent"
          title="Topological Execution Graph"
          highlightText="& System Architecture Flowchart"
          description="Interactive node-graph schematic of RUEXIS AI. Explore multi-modal PDF parsing, bipartite graph retrieval, autonomous agent DAG sequencing, dual-model code synthesis, and 3-layer virtual AST validation with real-time signal flow."
        />

        {/* Top Control Toolbar */}
        <FlowchartToolbar
          activePreset={activePreset}
          onPresetChange={handlePresetChange}
          displayMode={displayMode}
          onDisplayModeChange={setDisplayMode}
          isSimulating={isSimulating}
          onToggleSimulate={() => setIsSimulating(!isSimulating)}
          zoomScale={zoomScale}
          onZoomIn={() => setZoomScale((z) => Math.min(1.25, z + 0.1))}
          onZoomOut={() => setZoomScale((z) => Math.max(0.75, z - 0.1))}
          onResetZoom={() => setZoomScale(1)}
        />

        {/* View Mode: Interactive Graph Canvas OR Step Timeline */}
        {displayMode === "graph" ? (
          <FlowchartCanvas
            activePreset={activePreset}
            nodes={currentNodes}
            edges={currentEdges}
            selectedNodeId={selectedNodeId}
            hoveredNodeId={hoveredNodeId}
            activeStepIndex={activeStepIndex}
            isSimulating={isSimulating}
            zoomScale={zoomScale}
            onSelectNode={(id) => setSelectedNodeId(id)}
            onHoverNode={(id) => setHoveredNodeId(id)}
          />
        ) : (
          <FlowchartTimeline
            nodes={currentNodes}
            selectedNodeId={selectedNodeId}
            activeStepIndex={activeStepIndex}
            onSelectNode={(id) => setSelectedNodeId(id)}
          />
        )}

        {/* Simulation Real-Time Terminal Logs */}
        <FlowchartSimulationTerminal
          logs={simLogs}
          currentStep={activeStepIndex}
          totalSteps={currentNodes.length}
        />

        {/* Deep-Dive Inspector Panel with Next/Prev navigation */}
        <FlowchartInspector 
          activeNode={activeNode} 
          currentIndex={activeNodeIndex}
          totalNodes={currentNodes.length}
          onPrevNode={handlePrevNode}
          onNextNode={handleNextNode}
        />

      </div>
    </section>
  );
}
