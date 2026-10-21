import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { TierSelector } from '../../ui/TierSelector';
import { getPaperUrl, getPaperTaskUrl, getPaperWalkthroughUrl } from '../../../config/api';
import { UNIVERSAL_DEFAULT_HYPERPARAMETERS } from '../../../constants/defaults';
import { ScholarBadge, type ScholarMetadata } from './ScholarBadge';
import { ImplementationTabs } from './ImplementationTabs';
import { ParameterConfigForm } from './ParameterConfigForm';
import { ManifestViewer } from './ManifestViewer';
import { parseInlineMarkdown } from '../../../utils/markdownParser';

export const ReportView: React.FC = () => {
  const { 
    reportContent, 
    resetAnalysis, 
    selectedTier, 
    activePaperId, 
    triggerAnalysis, 
    isAnalyzing,
    analysisStatus,
    approveParameters,
    sendMessage,
    setActiveView,
    fetchKnowledgeGraph,
    manifest,
    fetchManifest
  } = usePanelStore();

  const [taskContent, setTaskContent] = useState<string>('');
  const [walkthroughContent, setWalkthroughContent] = useState<string>('');
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);
  const [customParams, setCustomParams] = useState<Record<string, string>>({
    ...UNIVERSAL_DEFAULT_HYPERPARAMETERS
  });
  const [extractedParams, setExtractedParams] = useState<Record<string, { value: string; status: string; confidence: number }> | null>(null);
  const [scholarMeta, setScholarMeta] = useState<ScholarMetadata | null>(null);

  useEffect(() => {
    if (activePaperId) {
      fetchManifest(activePaperId);
      if (analysisStatus === 'success') {
        fetchKnowledgeGraph(activePaperId);
      }
      const fetchScholarData = async () => {
        try {
          const resp = await fetch(getPaperUrl(activePaperId));
          if (resp.ok) {
            const data = await resp.json();
            
            // Extract Scholar info
            const meta = data.metadata || {};
            if (meta.scholar_tldr || meta.citation_count !== undefined) {
              setScholarMeta({
                tldr: meta.scholar_tldr,
                citations: meta.citation_count
              });
            }

            // Load extracted parameters if available
            if (data.extracted_parameters) {
              setExtractedParams(data.extracted_parameters);
              const dynamicParams: Record<string, string> = {};
              for (const [k, v] of Object.entries(data.extracted_parameters)) {
                if (v && typeof v === 'object' && 'value' in v) {
                  dynamicParams[k] = String((v as any).value);
                }
              }
              setCustomParams((prev) => ({
                ...prev,
                ...dynamicParams
              }));
            }
          }
        } catch {
          // ignore
        }
      };
      fetchScholarData();
    }
  }, [activePaperId, analysisStatus]);

  useEffect(() => {
    if (activePaperId && selectedTier === 'implement') {
      const fetchData = async () => {
        setIsLoadingFiles(true);
        try {
          const [tResp, wResp] = await Promise.all([
            fetch(getPaperTaskUrl(activePaperId)),
            fetch(getPaperWalkthroughUrl(activePaperId))
          ]);
          
          if (tResp.ok) {
            const tData = await tResp.json();
            setTaskContent(tData.content || '');
          } else {
            setTaskContent('### Implementation Task Checklist\n- [x] Document Extraction\n- [x] Structural Analysis\n- [ ] Code Synthesis');
          }
          if (wResp.ok) {
            const wData = await wResp.json();
            setWalkthroughContent(wData.content || '');
          } else {
            setWalkthroughContent('### Verification Walkthrough\nArchitectural blueprint staged for code synthesis and tensor validation.');
          }
        } catch (e) {
          console.error("Failed to fetch implements", e);
          setTaskContent('### Implementation Task Checklist\n- [x] Document Extraction\n- [x] Structural Analysis');
          setWalkthroughContent('### Verification Walkthrough\nPipeline ready.');
        } finally {
          setIsLoadingFiles(false);
        }
      };
      
      fetchData();
    }
  }, [activePaperId, selectedTier, isAnalyzing]);

  const [paramFilter, setParamFilter] = useState<'ALL' | 'EXPLICIT' | 'INFERRED' | 'DEFAULT'>('ALL');

  // Compute provenance breakdown statistics
  const provenanceStats = React.useMemo(() => {
    const keys = Object.keys(customParams);
    let explicit = 0;
    let inferred = 0;
    let defaults = 0;

    keys.forEach((k) => {
      const p = extractedParams?.[k];
      const st = p?.status?.toUpperCase();
      if (st === 'EXPLICIT') explicit++;
      else if (st === 'INFERRED' || st === 'DERIVED') inferred++;
      else defaults++;
    });

    return {
      total: keys.length,
      explicit,
      inferred,
      defaults,
      explicitPct: keys.length > 0 ? Math.round((explicit / keys.length) * 100) : 0,
      inferredPct: keys.length > 0 ? Math.round((inferred / keys.length) * 100) : 0,
      defaultsPct: keys.length > 0 ? Math.round((defaults / keys.length) * 100) : 0,
    };
  }, [customParams, extractedParams]);

  if (!activePaperId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-3">
        <span className="text-[10px] font-mono text-[var(--text-muted)]">No active paper staging workspace.</span>
      </div>
    );
  }

  // Provenance Summary Bar Component
  const renderProvenanceBar = () => {
    if (provenanceStats.total === 0) return null;
    return (
      <div className="flex flex-col gap-1.5 p-2.5 bg-[var(--bg-base)] rounded-xl border app-border text-[9px] font-mono">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-bold text-[var(--text-main)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Provenance Grounding:</span>
            <span className="text-emerald-400">{provenanceStats.explicit} Explicit</span>
            <span className="text-[var(--text-muted)]">|</span>
            <span className="text-amber-400">{provenanceStats.inferred} Inferred</span>
            <span className="text-[var(--text-muted)]">|</span>
            <span className="text-rose-400">{provenanceStats.defaults} Default</span>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1">
            {(['ALL', 'EXPLICIT', 'INFERRED', 'DEFAULT'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setParamFilter(mode)}
                className={`px-2 py-0.5 rounded-md text-[8px] font-bold transition-all cursor-pointer ${
                  paramFilter === mode
                    ? 'bg-[var(--accent)] text-white shadow-xs'
                    : 'bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-main)] border app-border'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        {/* Visual Progress Ratio Bar */}
        <div className="h-1.5 w-full bg-[var(--bg-card)] rounded-full overflow-hidden flex">
          <div
            style={{ width: `${provenanceStats.explicitPct}%` }}
            className="bg-emerald-400 transition-all duration-300"
            title={`${provenanceStats.explicit} Explicit (${provenanceStats.explicitPct}%)`}
          />
          <div
            style={{ width: `${provenanceStats.inferredPct}%` }}
            className="bg-amber-400 transition-all duration-300"
            title={`${provenanceStats.inferred} Inferred (${provenanceStats.inferredPct}%)`}
          />
          <div
            style={{ width: `${provenanceStats.defaultsPct}%` }}
            className="bg-rose-400 transition-all duration-300"
            title={`${provenanceStats.defaults} Default (${provenanceStats.defaultsPct}%)`}
          />
        </div>

        {/* Warning callout for ungrounded / default parameters */}
        {paramFilter === 'DEFAULT' && provenanceStats.defaults > 0 && (
          <div className="flex items-center gap-1.5 p-1.5 bg-rose-500/10 text-rose-300 border border-rose-500/20 rounded-lg text-[8px]">
            <span>⚠️</span>
            <span>
              {provenanceStats.defaults} parameters were not found verbatim in paper text and use baseline defaults.
            </span>
          </div>
        )}
      </div>
    );
  };

  // Render Detailed structural analysis tier
  if (selectedTier === 'detailed') {
    return (
      <div className="bg-[var(--bg-card)] border app-border rounded-xl p-4 flex flex-col gap-3 min-h-[350px] text-[var(--text-main)]">
        <div className="flex flex-col gap-2.5 border-b app-border pb-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider">
              PAPER STRUCTURAL ANALYSIS
            </span>
            <button 
              type="button"
              onClick={resetAnalysis} 
              className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
            >
              Reset Analysis
            </button>
          </div>
          <TierSelector />
          <ScholarBadge metadata={scholarMeta} />
        </div>

        {renderProvenanceBar()}

        {isAnalyzing ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-10">
            <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
            <span className="text-[10px] font-mono text-[var(--accent)] animate-pulse">
              Running Structural Analysis Pipeline...
            </span>
          </div>
        ) : analysisStatus === 'paused_for_review' ? (
          <ParameterConfigForm
            customParams={customParams}
            extractedParams={extractedParams}
            activeFilter={paramFilter}
            onChange={setCustomParams}
            onConfirm={() => approveParameters(customParams)}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-4 bg-[var(--bg-base)]/50 rounded-xl border border-dashed app-border">
            <div className="w-12 h-12 rounded-full bg-[var(--accent-subtle)] flex items-center justify-center border border-[var(--accent-border)] text-[var(--accent)] text-lg font-bold">
              📊
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold text-[var(--text-main)]">Staged for Structural Analysis</span>
              <span className="text-[10px] text-[var(--text-muted)] max-w-[280px]">
                The PDF has been parsed and cached. Trigger structural extraction to identify model architecture and verify GPU compatibility.
              </span>
            </div>
            <button
              type="button"
              onClick={() => triggerAnalysis()}
              className="mt-2 text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
            >
              Analyze Paper & Check Feasibility
            </button>
          </div>
        )}

        <ManifestViewer manifest={manifest} />
      </div>
    );
  }

  // Render Implementation tier
  if (selectedTier === 'implement') {
    const isTriggered = walkthroughContent && !walkthroughContent.includes("No verification checks have been run yet");

    return (
      <div className="bg-[var(--bg-card)] border app-border rounded-xl p-4 flex flex-col gap-3 min-h-[350px] text-[var(--text-main)]">
        <div className="flex flex-col gap-2.5 border-b app-border pb-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider">
              CODE GENERATION & RUN CODE
            </span>
            <button 
              type="button"
              onClick={resetAnalysis} 
              className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
            >
              Reset Analysis
            </button>
          </div>
          <TierSelector />
          <ScholarBadge metadata={scholarMeta} />
        </div>

        {isAnalyzing ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-10">
            <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
            <span className="text-[10px] font-mono text-[var(--accent)] animate-pulse">
              Running Multi-Agent Adaptation Pipeline...
            </span>
          </div>
        ) : !isTriggered ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 gap-3 bg-[var(--bg-base)]/50 rounded-xl border border-dashed app-border">
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold text-[var(--text-main)]">Implementation Blueprint Staged</span>
              <span className="text-[10px] text-[var(--text-muted)] max-w-[320px]">
                Review or adjust extracted hyperparameters below before generating the adapted PyTorch source code.
              </span>
            </div>

            <ParameterConfigForm
              customParams={customParams}
              extractedParams={extractedParams}
              onChange={setCustomParams}
              compactMode={true}
              confirmLabel="Get Code in Chat"
              onConfirm={() => {
                approveParameters(customParams);
                sendMessage("Generate complete PyTorch model implementation code for this paper.", true);
                setActiveView('chat');
              }}
            />
          </div>
        ) : (
          <ImplementationTabs
            walkthroughContent={walkthroughContent}
            taskContent={taskContent}
            isLoadingFiles={isLoadingFiles}
          />
        )}

        <ManifestViewer manifest={manifest} />
      </div>
    );
  }

  // Default Brief tier
  let displayMarkdown = reportContent || '';
  if (selectedTier === 'brief' && reportContent) {
    const lines = reportContent.split('\n');
    const briefLines: string[] = [];
    for (const line of lines) {
      if (line.includes('## 1. Extracted') || line.includes('## 1. Extracted Architectural Components')) {
        break;
      }
      briefLines.push(line);
    }
    displayMarkdown = briefLines.join('\n');
  }

  return (
    <div className="bg-[var(--bg-card)] border app-border rounded-xl p-4 flex flex-col gap-3 min-h-[350px] text-[var(--text-main)]">
      <div className="flex flex-col gap-2.5 border-b app-border pb-3">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider">
            EXECUTIVE PROPOSAL REPORT
          </span>
          <button 
            type="button"
            onClick={resetAnalysis} 
            className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
          >
            Reset Analysis
          </button>
        </div>
        <TierSelector />
        <ScholarBadge metadata={scholarMeta} />
      </div>

      <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[380px] p-2 bg-[var(--bg-base)]/40 rounded-lg border app-border text-[11px] leading-relaxed whitespace-pre-wrap">
        {displayMarkdown ? (
          displayMarkdown.split('\n').map((line, idx) => (
            <p key={idx} className="my-0.5">{parseInlineMarkdown(line)}</p>
          ))
        ) : (
          <span className="text-[var(--text-muted)] italic">No report available yet. Run ingestion first.</span>
        )}
      </div>

      <ManifestViewer manifest={manifest} />
    </div>
  );
};
