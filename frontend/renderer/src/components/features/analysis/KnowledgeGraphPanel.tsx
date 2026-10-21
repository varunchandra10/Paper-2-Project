import React, { useState, useEffect, useRef, useMemo } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import type { KnowledgeGraphNode, KnowledgeGraphEdge } from '../../../store/slices/knowledgeGraphSlice';
import {
  IconSearch,
  IconCheck,
  IconWarning,
  IconInfo2,
  IconClose,
  IconTasks,
  IconMaximize,
  IconMinimize
} from '../../ui/Icons';

const TIER_COLORS: Record<number, { bg: string; border: string; text: string; hex: string; name: string }> = {
  1: { bg: 'bg-amber-500/10', border: 'border-amber-500/40', text: 'text-amber-400', hex: '#F59E0B', name: 'Paper' },
  2: { bg: 'bg-gray-500/10', border: 'border-gray-500/40', text: 'text-gray-300', hex: '#6B7280', name: 'Section' },
  3: { bg: 'bg-purple-500/10', border: 'border-purple-500/40', text: 'text-purple-400', hex: '#8B5CF6', name: 'Concept' },
  4: { bg: 'bg-blue-500/10', border: 'border-blue-500/40', text: 'text-blue-400', hex: '#3B82F6', name: 'Component' },
  5: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/40', text: 'text-emerald-400', hex: '#10B981', name: 'Parameter' },
  6: { bg: 'bg-orange-500/10', border: 'border-orange-500/40', text: 'text-orange-400', hex: '#F97316', name: 'Dependency' },
  7: { bg: 'bg-pink-500/10', border: 'border-pink-500/40', text: 'text-pink-400', hex: '#EC4899', name: 'Implementation' },
};

interface PositionedNode extends KnowledgeGraphNode {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const KnowledgeGraphPanel: React.FC = () => {
  const {
    activePaperId,
    kgData,
    kgValidation,
    kgTraceResult,
    isKgLoading,
    isKgValidating,
    selectedNodeId,
    highlightedPath,
    visibleTiers,
    showBuildOrder,
    kgSearchQuery,
    fetchKnowledgeGraph,
    validateKg,
    traceEvidence,
    toggleTierVisibility,
    setShowBuildOrder,
    setKgSearchQuery,
    clearKgTrace,
    sendMessage,
    setActiveView
  } = usePanelStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 40, y: 40 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [showValidationModal, setShowValidationModal] = useState<boolean>(false);

  // Auto-fetch knowledge graph when paper ID is active and not yet loaded
  useEffect(() => {
    if (activePaperId && (!kgData || kgData.paper_id !== activePaperId)) {
      fetchKnowledgeGraph(activePaperId);
    }
  }, [activePaperId, kgData]);

  // Compute node positions using hierarchical tier layout
  const { positionedNodes, filteredEdges } = useMemo(() => {
    if (!kgData?.visualization?.nodes) {
      return { positionedNodes: [] as PositionedNode[], filteredEdges: [] as KnowledgeGraphEdge[] };
    }

    const rawNodes = kgData.visualization.nodes;
    const rawEdges = kgData.visualization.edges || [];

    // Filter nodes by visible tiers and search query
    const filteredNodes = rawNodes.filter((n) => {
      const matchesTier = visibleTiers.includes(n.tier);
      const matchesSearch =
        !kgSearchQuery ||
        n.label.toLowerCase().includes(kgSearchQuery.toLowerCase()) ||
        n.id.toLowerCase().includes(kgSearchQuery.toLowerCase()) ||
        n.node_type.toLowerCase().includes(kgSearchQuery.toLowerCase());
      return matchesTier && matchesSearch;
    });

    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
    const edges = rawEdges.filter(
      (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
    );

    // Group nodes by tier for level-by-level layout
    const tierBuckets: Record<number, KnowledgeGraphNode[]> = {
      1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []
    };

    filteredNodes.forEach((node) => {
      const t = Math.max(1, Math.min(7, node.tier || 4));
      tierBuckets[t].push(node);
    });

    const nodeWidth = 190;
    const nodeHeight = 64;
    const tierSpacingY = 120;
    const nodeSpacingX = 220;

    const positioned: PositionedNode[] = [];

    // Assign (x, y) coordinates with centered rows per tier
    Object.keys(tierBuckets).forEach((tierStr) => {
      const tierNum = Number(tierStr);
      const nodesInTier = tierBuckets[tierNum];
      const tierY = (tierNum - 1) * tierSpacingY + 60;
      const totalWidth = nodesInTier.length * nodeSpacingX;
      const startX = Math.max(40, 600 - totalWidth / 2);

      nodesInTier.forEach((node, idx) => {
        positioned.push({
          ...node,
          x: startX + idx * nodeSpacingX,
          y: tierY,
          width: nodeWidth,
          height: nodeHeight
        });
      });
    });

    return { positionedNodes: positioned, filteredEdges: edges };
  }, [kgData, visibleTiers, kgSearchQuery]);

  // Map for fast node coordinate lookups
  const nodePosMap = useMemo(() => {
    const map = new Map<string, PositionedNode>();
    positionedNodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [positionedNodes]);

  // Build order lookup map
  const buildOrderMap = useMemo(() => {
    const map = new Map<string, number>();
    if (kgData?.topology) {
      kgData.topology.forEach((item, idx) => {
        map.set(item.module, idx + 1);
      });
    }
    return map;
  }, [kgData]);

  // Pan and drag controls
  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag on canvas background
    if ((e.target as HTMLElement).tagName === 'svg' || (e.target as HTMLElement).id === 'kg-canvas-bg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomDelta = e.deltaY > 0 ? -0.08 : 0.08;
    setZoom((prev) => Math.min(2.0, Math.max(0.3, prev + zoomDelta)));
  };

  const handleFitView = () => {
    setZoom(0.85);
    setPan({ x: 60, y: 40 });
  };

  const handleNodeClick = (node: PositionedNode, e: React.MouseEvent) => {
    e.stopPropagation();
    if (activePaperId) {
      traceEvidence(activePaperId, node.id);
    }
  };

  const handleAskInChat = (quote: string, targetName: string) => {
    setActiveView('chat');
    sendMessage(`Based on the Knowledge Graph trace for "${targetName}", explain its grounding and architectural implementation:\n\n> "${quote}"`);
  };

  return (
    <div
      className={`flex flex-col bg-[var(--bg-base)] border app-border rounded-xl overflow-hidden font-sans select-none transition-all ${
        isFullscreen ? 'fixed inset-4 z-50 shadow-2xl bg-[var(--bg-card)]' : 'h-[540px] w-full'
      }`}
    >
      {/* ── Top Header & Command Toolbar ─────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-4 py-2.5 bg-[var(--bg-card)] border-b app-border shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent)] animate-pulse" />
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-[var(--text-main)]">
              7-Tier Knowledge Graph
            </h3>
          </div>

          {kgData && (
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-base)] px-2 py-0.5 rounded-md border app-border">
              <span>{kgData.nodes_count} Nodes</span>
              <span>•</span>
              <span>{kgData.edges_count} Edges</span>
            </div>
          )}

          {kgValidation && (
            <button
              onClick={() => setShowValidationModal(true)}
              className={`flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md border transition-all cursor-pointer ${
                kgValidation.consistent && kgValidation.dag_acyclic
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
              }`}
              title="Click to view consistency audit details"
            >
              {kgValidation.consistent && kgValidation.dag_acyclic ? (
                <IconCheck className="text-[11px]" />
              ) : (
                <IconWarning className="text-[11px]" />
              )}
              <span>{kgValidation.dag_acyclic ? 'DAG Acyclic' : 'Cycle Detected'}</span>
              {kgValidation.ungrounded_count > 0 && (
                <span className="bg-amber-500/30 text-amber-300 px-1 rounded text-[9px]">
                  {kgValidation.ungrounded_count} ungrounded
                </span>
              )}
            </button>
          )}
        </div>

        {/* Right Toolbar Controls */}
        <div className="flex items-center gap-2">
          {/* Quick Search */}
          <div className="relative w-36">
            <IconSearch className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-[10px]" />
            <input
              type="text"
              placeholder="Search graph..."
              value={kgSearchQuery}
              onChange={(e) => setKgSearchQuery(e.target.value)}
              className="w-full bg-[var(--bg-base)] border app-border pl-6 pr-2 py-1 rounded-lg text-[10px] text-[var(--text-main)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] font-mono"
            />
          </div>

          {/* Show Build Order Toggle */}
          <button
            onClick={() => setShowBuildOrder(!showBuildOrder)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold transition-all cursor-pointer ${
              showBuildOrder
                ? 'bg-[var(--accent)] text-white shadow-xs'
                : 'bg-[var(--bg-base)] text-[var(--text-muted)] hover:text-[var(--text-main)] border app-border'
            }`}
          >
            <IconTasks className="text-xs" />
            <span>Build Order</span>
          </button>

          {/* Validate Button */}
          <button
            onClick={() => activePaperId && validateKg(activePaperId)}
            disabled={isKgValidating || !activePaperId}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold bg-[var(--bg-base)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border app-border transition-all cursor-pointer disabled:opacity-50"
            title="Run Knowledge Graph structural validation"
          >
            {isKgValidating ? (
              <div className="w-3 h-3 rounded-full border border-[var(--accent)] border-t-transparent animate-spin" />
            ) : (
              <IconCheck className="text-xs text-[var(--accent)]" />
            )}
            <span>Validate</span>
          </button>

          {/* Fit View */}
          <button
            onClick={handleFitView}
            className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border app-border transition-all cursor-pointer"
            title="Fit graph to view"
          >
            <span className="text-[10px] font-mono font-bold px-1">Fit</span>
          </button>

          {/* Zoom controls */}
          <div className="flex items-center bg-[var(--bg-base)] border app-border rounded-lg p-0.5 text-[10px] font-mono">
            <button
              onClick={() => setZoom((z) => Math.max(0.3, z - 0.1))}
              className="px-1.5 py-0.5 hover:text-[var(--text-main)] text-[var(--text-muted)] cursor-pointer"
            >
              -
            </button>
            <span className="px-1 text-[var(--text-muted)]">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom((z) => Math.min(2.0, z + 0.1))}
              className="px-1.5 py-0.5 hover:text-[var(--text-main)] text-[var(--text-muted)] cursor-pointer"
            >
              +
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border app-border transition-all cursor-pointer"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <IconMinimize className="text-xs" /> : <IconMaximize className="text-xs" />}
          </button>
        </div>
      </div>

      {/* ── Tier Filter Chips Bar ───────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-1.5 px-4 py-1.5 bg-[var(--bg-card)]/60 border-b app-border text-[9px] font-mono shrink-0">
        <span className="text-[var(--text-muted)] mr-1 uppercase font-bold text-[8px] tracking-wider">
          Tiers:
        </span>
        {[1, 2, 3, 4, 5, 6, 7].map((tier) => {
          const info = TIER_COLORS[tier];
          const isVisible = visibleTiers.includes(tier);
          return (
            <button
              key={tier}
              onClick={() => toggleTierVisibility(tier)}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-md border transition-all cursor-pointer ${
                isVisible
                  ? `${info.bg} ${info.text} ${info.border} font-bold shadow-xs`
                  : 'bg-[var(--bg-base)] text-[var(--text-muted)] border-transparent opacity-40 hover:opacity-80'
              }`}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: info.hex }}
              />
              <span>
                T{tier}: {info.name}
              </span>
            </button>
          );
        })}
        {highlightedPath.length > 0 && (
          <button
            onClick={clearKgTrace}
            className="ml-auto text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer font-bold"
          >
            <IconClose className="text-[10px]" />
            <span>Clear Trace ({highlightedPath.length} nodes)</span>
          </button>
        )}
      </div>

      {/* ── Main Canvas & Interactive Graph Viewport ─────────────────── */}
      <div
        ref={containerRef}
        id="kg-canvas-bg"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="flex-1 relative overflow-hidden bg-[var(--bg-base)] cursor-grab active:cursor-grabbing select-none"
        style={{
          backgroundImage:
            'radial-gradient(var(--border-color) 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      >
        {isKgLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[var(--bg-base)]/80 backdrop-blur-sm z-20">
            <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
            <span className="text-xs font-mono text-[var(--text-muted)]">
              Constructing 7-Tier Knowledge Graph...
            </span>
          </div>
        ) : positionedNodes.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-[var(--text-muted)] z-10">
            <IconInfo2 className="text-3xl opacity-30 text-[var(--accent)]" />
            <span className="text-xs font-mono">No knowledge graph data loaded.</span>
            <button
              onClick={() => activePaperId && fetchKnowledgeGraph(activePaperId)}
              className="mt-2 px-3 py-1 bg-[var(--accent)] text-white text-xs font-mono rounded-lg cursor-pointer"
            >
              Build Knowledge Graph
            </button>
          </div>
        ) : (
          <div
            className="absolute origin-top-left transition-transform duration-75 ease-out"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`
            }}
          >
            {/* SVG Link Layer */}
            <svg
              className="absolute top-0 left-0 overflow-visible pointer-events-none"
              style={{ width: '2400px', height: '1200px' }}
            >
              <defs>
                <marker
                  id="kg-arrow"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="5"
                  markerHeight="5"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="var(--text-muted)" opacity="0.6" />
                </marker>
                <marker
                  id="kg-arrow-highlight"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 1 L 8 5 L 0 9 z" fill="#F59E0B" />
                </marker>
              </defs>

              {filteredEdges.map((edge) => {
                const src = nodePosMap.get(edge.source);
                const tgt = nodePosMap.get(edge.target);
                if (!src || !tgt) return null;

                const x1 = src.x + src.width / 2;
                const y1 = src.y + src.height;
                const x2 = tgt.x + tgt.width / 2;
                const y2 = tgt.y;

                const isPathActive =
                  highlightedPath.includes(edge.source) &&
                  highlightedPath.includes(edge.target);

                // Smooth cubic bezier vertical curve
                const cy1 = y1 + Math.abs(y2 - y1) * 0.5;
                const cy2 = y2 - Math.abs(y2 - y1) * 0.5;
                const d = `M ${x1} ${y1} C ${x1} ${cy1}, ${x2} ${cy2}, ${x2} ${y2}`;

                return (
                  <g key={edge.id}>
                    <path
                      d={d}
                      fill="none"
                      stroke={isPathActive ? '#F59E0B' : 'var(--border-color)'}
                      strokeWidth={isPathActive ? 2.5 : 1.2}
                      strokeDasharray={edge.relation === 'configures_component' ? '4 2' : undefined}
                      markerEnd={isPathActive ? 'url(#kg-arrow-highlight)' : 'url(#kg-arrow)'}
                      className="transition-all duration-300"
                    />
                    {edge.relation && (
                      <text
                        x={(x1 + x2) / 2}
                        y={(y1 + y2) / 2}
                        fill={isPathActive ? '#F59E0B' : 'var(--text-muted)'}
                        fontSize="8"
                        fontFamily="monospace"
                        textAnchor="middle"
                        className="select-none opacity-80"
                      >
                        {edge.relation}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Positioned Node Cards */}
            {positionedNodes.map((node) => {
              const info = TIER_COLORS[node.tier] || TIER_COLORS[4];
              const isSelected = selectedNodeId === node.id;
              const isPathActive = highlightedPath.includes(node.id);
              const buildStep = buildOrderMap.get(node.id) || buildOrderMap.get(node.label);

              return (
                <div
                  key={node.id}
                  onClick={(e) => handleNodeClick(node, e)}
                  style={{
                    position: 'absolute',
                    left: `${node.x}px`,
                    top: `${node.y}px`,
                    width: `${node.width}px`,
                    minHeight: `${node.height}px`
                  }}
                  className={`flex flex-col justify-between p-2.5 rounded-xl border transition-all duration-200 cursor-pointer backdrop-blur-md shadow-sm select-none ${
                    isSelected
                      ? 'ring-2 ring-[var(--accent)] shadow-lg scale-105 z-30 bg-[var(--bg-card)]'
                      : isPathActive
                      ? 'ring-2 ring-amber-400 shadow-md scale-102 z-20 bg-[var(--bg-card)]'
                      : 'hover:scale-102 hover:shadow-md z-10 bg-[var(--bg-card)]/90 hover:bg-[var(--bg-card)]'
                  } ${node.tier === 1 ? 'border-amber-500/50' : 'app-border'}`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span
                      className={`text-[8px] font-mono px-1.5 py-0.2 rounded-full font-bold uppercase tracking-wider border ${info.bg} ${info.text} ${info.border}`}
                    >
                      {node.badge || info.name}
                    </span>

                    {showBuildOrder && buildStep && (
                      <span className="text-[8px] font-mono font-bold px-1.5 py-0.2 bg-[var(--accent-subtle)] text-[var(--accent)] rounded-full border border-[var(--accent-border)]">
                        #{buildStep}
                      </span>
                    )}

                    {isPathActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                    )}
                  </div>

                  <div className="text-[11px] font-mono font-bold text-[var(--text-main)] truncate leading-tight">
                    {node.label}
                  </div>

                  {node.attributes?.value && (
                    <div className="text-[9px] font-mono text-emerald-400 truncate mt-0.5">
                      = {String(node.attributes.value)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Evidence Trace Provenance Card (Floating Bottom Overlay) ── */}
        {kgTraceResult && kgTraceResult.found && (
          <div className="absolute left-4 right-4 bottom-4 max-w-xl bg-[var(--bg-card)] border border-amber-500/40 rounded-xl p-3.5 shadow-xl backdrop-blur-xl z-30 flex flex-col gap-2 font-mono text-[11px]">
            <div className="flex items-center justify-between border-b app-border pb-1.5">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="font-bold text-[var(--text-main)]">
                  Evidence Provenance Trace
                </span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300">
                  {kgTraceResult.target_type}
                </span>
              </div>
              <button
                onClick={clearKgTrace}
                className="text-[var(--text-muted)] hover:text-[var(--text-main)] cursor-pointer"
              >
                <IconClose className="text-sm" />
              </button>
            </div>

            {/* Provenance Path Breadcrumbs */}
            <div className="flex flex-wrap items-center gap-1 text-[9px] text-[var(--text-muted)]">
              <span className="text-amber-400 font-bold">Path:</span>
              {kgTraceResult.provenance_path?.map((step, idx) => (
                <React.Fragment key={idx}>
                  <span className="px-1 py-0.2 bg-[var(--bg-base)] rounded text-[var(--text-main)] border app-border">
                    {step}
                  </span>
                  {idx < kgTraceResult.provenance_path.length - 1 && (
                    <span className="text-amber-400">→</span>
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* Exact Evidence Quote */}
            {kgTraceResult.evidence_quote && (
              <div className="bg-[var(--bg-base)] p-2.5 rounded-lg border app-border text-[10px] text-[var(--text-main)] leading-relaxed italic border-l-2 border-l-amber-400">
                "{kgTraceResult.evidence_quote}"
              </div>
            )}

            <div className="flex items-center justify-between pt-1">
              <span className="text-[9px] text-[var(--text-muted)]">
                Grounding Section:{' '}
                <strong className="text-[var(--text-main)]">
                  {kgTraceResult.grounding_section || 'Method'}
                </strong>
              </span>

              <button
                onClick={() =>
                  handleAskInChat(
                    kgTraceResult.evidence_quote || '',
                    kgTraceResult.target
                  )
                }
                className="px-2.5 py-1 bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-white rounded-lg text-[10px] font-bold transition-all cursor-pointer"
              >
                Inspect in Chat →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Validation Audit Modal ──────────────────────────────────── */}
      {showValidationModal && kgValidation && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-md bg-[var(--bg-card)] border app-border rounded-xl p-4 shadow-2xl flex flex-col gap-3 font-mono text-[11px]">
            <div className="flex items-center justify-between border-b app-border pb-2">
              <div className="flex items-center gap-2">
                <IconCheck className="text-emerald-400 text-base" />
                <h4 className="font-bold text-[var(--text-main)] text-xs">
                  Knowledge Graph Consistency Audit
                </h4>
              </div>
              <button
                onClick={() => setShowValidationModal(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-main)] cursor-pointer"
              >
                <IconClose className="text-base" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="p-2 bg-[var(--bg-base)] rounded-lg border app-border">
                <span className="text-[var(--text-muted)] block">DAG Acyclicity</span>
                <strong className={kgValidation.dag_acyclic ? 'text-emerald-400' : 'text-red-400'}>
                  {kgValidation.dag_acyclic ? 'Strictly Acyclic (Valid)' : 'Cycle Detected'}
                </strong>
              </div>

              <div className="p-2 bg-[var(--bg-base)] rounded-lg border app-border">
                <span className="text-[var(--text-muted)] block">Grounding Rate</span>
                <strong className="text-emerald-400">
                  {kgValidation.grounded_parameters} / {kgValidation.parameters_count} (
                  {kgValidation.parameters_count > 0
                    ? Math.round((kgValidation.grounded_parameters / kgValidation.parameters_count) * 100)
                    : 100}
                  %)
                </strong>
              </div>
            </div>

            {kgValidation.warnings && kgValidation.warnings.length > 0 && (
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-amber-400 font-bold">Warnings:</span>
                <div className="max-h-24 overflow-y-auto bg-[var(--bg-base)] p-2 rounded-lg border app-border flex flex-col gap-1 text-[9px] text-[var(--text-muted)]">
                  {kgValidation.warnings.map((w, idx) => (
                    <div key={idx} className="flex items-start gap-1">
                      <span className="text-amber-400">•</span>
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => setShowValidationModal(false)}
              className="mt-2 py-1.5 bg-[var(--accent)] text-white font-bold rounded-lg cursor-pointer text-center text-xs"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
