import React, { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';
import {
  IconCopy,
  IconCheck,
  IconMaximize,
  IconClose,
  IconTerminal
} from './Icons';

interface MermaidRendererProps {
  code: string;
}

/**
 * Deep sanitization and auto-repair pipeline for LLM-generated Mermaid code.
 * Ensures strict compliance with Mermaid syntax, quoting all labels and fixing subgraphs.
 */
function sanitizeMermaidCode(text: string): string {
  let cleaned = text.trim();

  // Strip fences
  cleaned = cleaned.replace(/^```(?:mermaid)?\s*/i, '').replace(/```\s*$/, '').trim();

  // Ensure diagram declaration exists
  const headerMatch = cleaned.match(/^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitGraph)\b/i);
  if (!headerMatch) {
    cleaned = 'flowchart TD\n' + cleaned;
  }

  // 1. Expand multiple '&' connections across lines: e.g. "A & B & C --> D"
  const lines = cleaned.split('\n');
  const expandedLines: string[] = [];
  for (const l of lines) {
    const andConnMatch = l.match(/^(\s*)([A-Za-z0-9_]+(?:\s*&\s*[A-Za-z0-9_]+)+)\s*(-->|---|-.->|==>)\s*(.+)$/);
    if (andConnMatch) {
      const indent = andConnMatch[1];
      const sources = andConnMatch[2].split('&').map(s => s.trim());
      const arrow = andConnMatch[3];
      const target = andConnMatch[4].trim();
      for (const src of sources) {
        expandedLines.push(`${indent}${src} ${arrow} ${target}`);
      }
    } else {
      expandedLines.push(l);
    }
  }

  // 2. Sanitize line by line
  const sanitizedLines: string[] = [];
  let subCount = 0;

  for (let l of expandedLines) {
    // A. Repair subgraph lines:
    // e.g. "subgraph Transformer Block (e.g., Attention)" -> "subgraph sub_1 ["Transformer Block (e.g., Attention)"]"
    const subMatch = l.match(/^(\s*subgraph)\s+([^"\n\[]+)$/i);
    if (subMatch) {
      const indent = subMatch[1];
      const rawTitle = subMatch[2].trim();
      if (/[\s\(\):,\.]/.test(rawTitle) && !rawTitle.includes('[') && !rawTitle.includes('"')) {
        subCount++;
        const safeId = `sub_${subCount}`;
        const cleanTitle = rawTitle.replace(/"/g, "'");
        l = `${indent} ${safeId} ["${cleanTitle}"]`;
      }
    }

    // B. Quote unquoted square brackets:
    // e.g. Node[Some text (with info) / other] -> Node["Some text (with info) / other"]
    l = l.replace(/\b([A-Za-z0-9_]+)\[([^"\]\n][^\]\n]*)\]/g, (_match, id, label) => {
      const safeLabel = label.replace(/"/g, "'").trim();
      return `${id}["${safeLabel}"]`;
    });

    // C. Quote unquoted parens circles:
    // e.g. Node((Some text (parens))) -> Node(["Some text"])
    l = l.replace(/\b([A-Za-z0-9_]+)\(\(([^"\)\n][^\)\n]*)\)\)/g, (_match, id, label) => {
      const safeLabel = label.replace(/"/g, "'").trim();
      return `${id}(("${safeLabel}"))`;
    });

    // D. Quote unquoted link labels:
    // e.g. -->|some (label)| -> -->|"some (label)"|
    l = l.replace(/(-->|---|-.->|==>)\|([^"\|\n]+)\|/g, (_match, arrow, label) => {
      const safeLabel = label.replace(/"/g, "'").trim();
      return `${arrow}|"${safeLabel}"|`;
    });

    sanitizedLines.push(l);
  }

  let result = sanitizedLines.join('\n');

  // 3. Ensure matching subgraphs and ends
  const openSubs = (result.match(/\bsubgraph\b/g) || []).length;
  const closeSubs = (result.match(/\bend\b/g) || []).length;
  if (openSubs > closeSubs) {
    for (let i = 0; i < openSubs - closeSubs; i++) {
      result += '\n    end';
    }
  }

  return result;
}

export const MermaidRenderer: React.FC<MermaidRendererProps> = ({ code }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const modalContainerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [renderError, setRenderError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showCode, setShowCode] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const rawId = useId().replace(/:/g, '');
  const uniqueId = `mermaid_${rawId}`;

  // Sanitize and heal code
  const cleanCode = React.useMemo(() => {
    return sanitizeMermaidCode(code);
  }, [code]);

  useEffect(() => {
    let isMounted = true;

    const renderDiagram = async () => {
      if (!cleanCode) return;

      try {
        const isDark =
          !document.body.classList.contains('theme-light') ||
          document.documentElement.classList.contains('dark') ||
          document.documentElement.getAttribute('data-theme')?.startsWith('d');

        mermaid.initialize({
          startOnLoad: false,
          theme: isDark ? 'dark' : 'neutral',
          securityLevel: 'loose',
          fontFamily: 'inherit',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
          },
          themeVariables: isDark
            ? {
                primaryColor: '#3b82f6',
                primaryTextColor: '#f8fafc',
                primaryBorderColor: '#60a5fa',
                lineColor: '#94a3b8',
                secondaryColor: '#1e293b',
                tertiaryColor: '#0f172a'
              }
            : {
                primaryColor: '#2563eb',
                primaryTextColor: '#0f172a',
                primaryBorderColor: '#3b82f6',
                lineColor: '#64748b'
              }
        });

        // Use a random render ID to prevent DOM collision across chat re-renders
        const renderId = `${uniqueId}_${Math.random().toString(36).substring(2, 7)}`;
        
        try {
          const { svg } = await mermaid.render(renderId, cleanCode);
          if (isMounted) {
            setSvgContent(svg);
            setRenderError(null);
          }
        } catch (_primaryErr) {
          // Fallback: If nested subgraphs fail, try flattening subgraphs to preserve node connections
          const fallbackCode = cleanCode.replace(/^\s*(subgraph\b[^\n]*|end\s*)$/gm, '');
          const fallbackId = `${uniqueId}_fb_${Math.random().toString(36).substring(2, 7)}`;
          const { svg } = await mermaid.render(fallbackId, fallbackCode);
          if (isMounted) {
            setSvgContent(svg);
            setRenderError(null);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const errMsg = err instanceof Error ? err.message : String(err);
          const simpleErr = errMsg.split('\n')[0] || 'Invalid Mermaid syntax';
          setRenderError(simpleErr);
          setSvgContent('');
        }
      } finally {
        // Clean up temporary mermaid error elements if any were injected into body
        const leaked = document.querySelectorAll(`[id*="${uniqueId}"], [id*="dmermaid"]`);
        leaked.forEach(el => el.remove());
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
      const errEl = document.getElementById(`d${uniqueId}`);
      if (errEl) errEl.remove();
    };
  }, [cleanCode, uniqueId]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(cleanCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore clipboard fallback
    }
  };

  return (
    <div className="my-3 flex flex-col w-full max-w-full text-left rounded-xl overflow-hidden border app-border bg-[var(--bg-card)]/90 shadow-md">
      {/* ── Header Toolbar ── */}
      <div className="flex justify-between items-center px-3 py-1.5 bg-[var(--bg-base)]/70 border-b app-border select-none">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
          <span className="text-[10px] font-mono text-[var(--accent)] font-bold uppercase tracking-wider">
            Architecture Diagram
          </span>
        </div>

        <div className="flex items-center gap-1">
          {/* Toggle Raw Code */}
          <button
            onClick={() => setShowCode(!showCode)}
            className={`px-2 py-0.5 rounded text-[9.5px] font-mono transition-colors cursor-pointer ${
              showCode
                ? 'bg-[var(--accent)] text-white font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
            }`}
            title="Toggle between diagram and Mermaid code"
          >
            <span className="flex items-center gap-1">
              <IconTerminal className="text-[10px]" />
              {showCode ? 'DIAGRAM' : 'CODE'}
            </span>
          </button>

          {/* Fullscreen Expand */}
          {!renderError && svgContent && !showCode && (
            <button
              onClick={() => {
                setIsFullscreen(true);
                setZoomLevel(1);
              }}
              className="px-2 py-0.5 rounded text-[9.5px] font-mono text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-colors cursor-pointer"
              title="Expand architecture in full screen modal"
            >
              <span className="flex items-center gap-1">
                <IconMaximize className="text-[10px]" />
                EXPAND
              </span>
            </button>
          )}

          {/* Copy Mermaid Source */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[9.5px] font-mono text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors px-2 py-0.5 rounded hover:bg-[var(--accent-subtle)] cursor-pointer"
            title="Copy Mermaid source code"
          >
            {copied ? (
              <>
                <IconCheck className="text-emerald-400 text-[10px]" />
                <span className="text-emerald-400 font-bold">COPIED</span>
              </>
            ) : (
              <>
                <IconCopy className="text-[10px]" />
                <span>COPY</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Content View ── */}
      <div className="p-3 bg-[var(--bg-base)]/40 overflow-x-auto min-w-0">
        {showCode ? (
          <pre className="text-[11px] font-mono text-[var(--text-main)] leading-relaxed select-text whitespace-pre overflow-x-auto p-2 rounded bg-[var(--bg-card)] border app-border">
            <code>{cleanCode}</code>
          </pre>
        ) : renderError ? (
          <div className="flex flex-col gap-2 p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 text-xs">
            <span className="font-mono text-amber-400 font-semibold flex items-center gap-1.5">
              ⚠️ Diagram syntax notice: {renderError}
            </span>
            <pre className="text-[10.5px] font-mono text-[var(--text-muted)] bg-[var(--bg-card)]/80 p-2 rounded border app-border overflow-x-auto whitespace-pre">
              <code>{cleanCode}</code>
            </pre>
          </div>
        ) : svgContent ? (
          <div
            ref={containerRef}
            className="mermaid-svg-container flex justify-center items-center py-3 w-full max-w-full overflow-x-auto select-none [&>svg]:max-w-full [&>svg]:h-auto [&>svg]:transition-transform"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="flex justify-center items-center py-6 text-xs text-[var(--text-muted)] font-mono animate-pulse">
            Rendering Architecture Flowchart...
          </div>
        )}
      </div>

      {/* ── Fullscreen Interactive Modal ── */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col p-4 animate-fade-in">
          {/* Modal Header */}
          <div className="flex justify-between items-center pb-3 border-b border-white/10 px-2 select-none">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
                Architecture Diagram — Full View
              </span>
            </div>

            {/* Zoom & Close controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.2))}
                className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs font-mono transition-colors cursor-pointer"
                title="Zoom Out"
              >
                -
              </button>
              <span className="text-xs font-mono text-white/70 min-w-12 text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(3.0, z + 0.2))}
                className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs font-mono transition-colors cursor-pointer"
                title="Zoom In"
              >
                +
              </button>
              <button
                onClick={() => setZoomLevel(1)}
                className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs font-mono transition-colors cursor-pointer"
                title="Reset Zoom"
              >
                Reset
              </button>
              <button
                onClick={() => setIsFullscreen(false)}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-red-500/80 text-white transition-colors cursor-pointer ml-3"
                title="Close Fullscreen"
              >
                <IconClose className="text-sm" />
              </button>
            </div>
          </div>

          {/* Modal SVG Body */}
          <div className="flex-1 overflow-auto flex items-center justify-center p-6">
            <div
              ref={modalContainerRef}
              style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
              className="transition-transform duration-150 flex items-center justify-center max-w-full [&>svg]:max-w-none"
              dangerouslySetInnerHTML={{ __html: svgContent }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
