import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { TierSelector } from '../../ui/TierSelector';

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
    setActiveView
  } = usePanelStore();
  const [taskContent, setTaskContent] = useState<string>('');
  const [walkthroughContent, setWalkthroughContent] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'walkthrough' | 'checklist'>('walkthrough');
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);

  const [customParams, setCustomParams] = useState({
    learning_rate: '0.0002',
    batch_size: '4',
    optimizer: 'AdamW',
    loss: 'BCEDiceLoss',
    epochs: '50',
    model: 'Swin-T',
    dataset: 'LEVIR-CD',
    scheduler: 'CosineAnnealing',
    input_size: '256x256',
    augmentation: 'RandomFlip',
    hardware: 'NVIDIA RTX'
  });

  const [extractedParams, setExtractedParams] = useState<Record<string, { value: string; status: string; confidence: number }> | null>(null);
  const [scholarMeta, setScholarMeta] = useState<{ tldr?: string; citations?: number } | null>(null);

  useEffect(() => {
    if (activePaperId) {
      const fetchScholarData = async () => {
        try {
          const apiBase = (typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:'))
            ? 'http://localhost:8000'
            : '/api';
          const resp = await fetch(`${apiBase}/history/${activePaperId}`);
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
              setCustomParams({
                learning_rate: data.extracted_parameters.learning_rate?.value || '0.0002',
                batch_size: data.extracted_parameters.batch_size?.value || '4',
                optimizer: data.extracted_parameters.optimizer?.value || 'AdamW',
                loss: data.extracted_parameters.loss?.value || 'BCEDiceLoss',
                epochs: data.extracted_parameters.epochs?.value || '50',
                model: data.extracted_parameters.model?.value || 'Swin-T',
                dataset: data.extracted_parameters.dataset?.value || 'LEVIR-CD',
                scheduler: data.extracted_parameters.scheduler?.value || 'CosineAnnealing',
                input_size: data.extracted_parameters.input_size?.value || '256x256',
                augmentation: data.extracted_parameters.augmentation?.value || 'RandomFlip',
                hardware: data.extracted_parameters.hardware?.value || 'NVIDIA RTX'
              });
            }
          }
        } catch (e) {
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
          const apiBase = (typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:'))
            ? 'http://localhost:8000'
            : '/api';
          
          const [tResp, wResp] = await Promise.all([
            fetch(`${apiBase}/history/${activePaperId}/task`),
            fetch(`${apiBase}/history/${activePaperId}/walkthrough`)
          ]);
          
          if (tResp.ok) {
            const tData = await tResp.json();
            setTaskContent(tData.content || '');
          }
          if (wResp.ok) {
            const wData = await wResp.json();
            setWalkthroughContent(wData.content || '');
          }
        } catch (e) {
          console.error("Failed to fetch implements", e);
        } finally {
          setIsLoadingFiles(false);
        }
      };
      
      fetchData();
    }
  }, [activePaperId, selectedTier, isAnalyzing]);

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'EXPLICIT': return 'border-emerald-500/25 bg-emerald-500/5 text-emerald-400';
      case 'INFERRED':
      case 'DERIVED': return 'border-sky-500/25 bg-sky-500/5 text-sky-400';
      case 'ASSUMED': return 'border-amber-500/25 bg-amber-500/5 text-amber-400';
      case 'UNKNOWN': return 'border-rose-500/25 bg-rose-500/5 text-rose-400';
      default: return 'border-border/30 bg-muted/5 text-foreground/50';
    }
  };

  if (!activePaperId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-3">
        <span className="text-[10px] font-mono text-foreground/40">No active paper staging workspace.</span>
      </div>
    );
  }

  // Render Feasibility tier with parameter review form
  if (selectedTier === 'feasibility') {
    return (
      <div className="bg-[var(--bg-card)] border app-border rounded-xl p-4 flex flex-col gap-3 min-h-[350px] text-[var(--text-main)]">
        <div className="flex flex-col gap-2.5 border-b app-border pb-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider">PAPER STRUCTURAL ANALYSIS</span>
            <button 
              onClick={resetAnalysis} 
              className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
            >
              Reset Analysis
            </button>
          </div>
          <TierSelector />
          {scholarMeta && (scholarMeta.tldr || scholarMeta.citations !== undefined) && (
            <div className="bg-[var(--accent-subtle)] border border-[var(--accent-border)] rounded-lg p-2.5 flex flex-col gap-1 text-left text-[10px] my-1">
              <div className="flex justify-between items-center">
                <span className="font-mono font-bold text-[var(--accent)] uppercase text-[9px]">Academic Reception (Semantic Scholar)</span>
                {scholarMeta.citations !== undefined && (
                  <span className="bg-[var(--accent-subtle)] text-[var(--accent)] font-mono text-[8px] px-2 py-0.5 rounded-full border border-[var(--accent-border)]">
                    {scholarMeta.citations} Citations
                  </span>
                )}
              </div>
              {scholarMeta.tldr && (
                <p className="text-[var(--text-main)] font-sans text-[10px] italic leading-tight">
                  "{scholarMeta.tldr}"
                </p>
              )}
            </div>
          )}
        </div>

        {isAnalyzing ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-10">
            <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin"></div>
            <span className="text-[10px] font-mono text-[var(--accent)] animate-pulse">Running Structural Analysis Pipeline...</span>
          </div>
        ) : analysisStatus === 'paused_for_review' ? (
          <div className="flex-1 flex flex-col gap-3">
            <div className="flex flex-col gap-0.5 text-left pb-1">
              <span className="text-xs font-bold text-[var(--text-main)]">Review Extracted Hyperparameters</span>
              <span className="text-[9px] text-[var(--text-muted)] leading-tight">
                Review or adjust target attributes before executing the hardware resource compatibility analysis.
              </span>
            </div>

            <div className="flex-1 overflow-y-auto max-h-[360px] pr-1.5 scrollbar-thin flex flex-col gap-3">
              <div className="grid grid-cols-2 gap-2 text-left">
                {Object.keys(customParams).map((paramKey) => {
                  const key = paramKey as keyof typeof customParams;
                  const item = extractedParams?.[key];
                  const label = key.toUpperCase().replace('_', ' ');

                  return (
                    <div key={key} className="bg-[var(--bg-base)]/50 border app-border rounded-lg p-2 flex flex-col gap-1.5 transition-all">
                      <div className="flex justify-between items-center gap-1.5">
                        <span className="text-[8px] font-mono font-bold text-[var(--accent)]">{label}</span>
                        {item && (
                          <span className={`text-[7px] font-mono font-semibold border px-1.5 py-0.2 rounded-full leading-none uppercase ${getStatusColor(item.status)}`}>
                            {item.status}
                          </span>
                        )}
                      </div>
                      <input 
                        type="text" 
                        value={customParams[key]} 
                        onChange={(e) => setCustomParams({...customParams, [key]: e.target.value})}
                        className="w-full bg-[var(--bg-card)] border app-border rounded px-2.5 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t app-border pt-2">
              <button
                onClick={() => approveParameters(customParams)}
                className="text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2.5 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
              >
                Confirm & Run Feasibility Check
              </button>
            </div>
          </div>
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
              onClick={() => triggerAnalysis()}
              className="mt-2 text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
            >
              Analyze Paper & Check Feasibility
            </button>
          </div>
        )}
      </div>
    );
  }

  // Render Implementation tier with PyTorch templates and optimized constraints
  if (selectedTier === 'implement') {
    const isTriggered = walkthroughContent && !walkthroughContent.includes("No verification checks have been run yet");

    return (
      <div className="bg-[var(--bg-card)] border app-border rounded-xl p-4 flex flex-col gap-3 min-h-[350px] text-[var(--text-main)]">
        <div className="flex flex-col gap-2.5 border-b app-border pb-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wider">CODE GENERATION & RUN CODE</span>
            <button 
              onClick={resetAnalysis} 
              className="text-[8px] font-mono font-bold bg-[var(--accent-subtle)] hover:bg-[var(--accent)] hover:text-white text-[var(--accent)] border border-[var(--accent-border)] px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
            >
              Reset Analysis
            </button>
          </div>
          <TierSelector />
          {scholarMeta && (scholarMeta.tldr || scholarMeta.citations !== undefined) && (
            <div className="bg-[var(--accent-subtle)] border border-[var(--accent-border)] rounded-lg p-2.5 flex flex-col gap-1 text-left text-[10px] my-1">
              <div className="flex justify-between items-center">
                <span className="font-mono font-bold text-[var(--accent)] uppercase text-[9px]">Academic Reception (Semantic Scholar)</span>
                {scholarMeta.citations !== undefined && (
                  <span className="bg-[var(--accent-subtle)] text-[var(--accent)] font-mono text-[8px] px-2 py-0.5 rounded-full border border-[var(--accent-border)]">
                    {scholarMeta.citations} Citations
                  </span>
                )}
              </div>
              {scholarMeta.tldr && (
                <p className="text-[var(--text-main)] font-sans text-[10px] italic leading-tight">
                  "{scholarMeta.tldr}"
                </p>
              )}
            </div>
          )}
        </div>

        {isAnalyzing ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-10">
            <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin"></div>
            <span className="text-[10px] font-mono text-[var(--accent)] animate-pulse">Running Multi-Agent Adaptation Pipeline...</span>
          </div>
        ) : !isTriggered ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 gap-3 bg-[var(--bg-base)]/50 rounded-xl border border-dashed app-border">
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold text-[var(--text-main)]">Implementation Blueprint Staged</span>
              <span className="text-[10px] text-[var(--text-muted)] max-w-[320px]">
                Review or adjust extracted hyperparameters below before generating the adapted PyTorch source code.
              </span>
            </div>

            <div className="w-full max-w-xs flex flex-col gap-2 bg-[var(--bg-base)]/80 p-3 rounded-lg border app-border text-left">
              <span className="text-[9px] font-mono font-bold text-[var(--accent)] uppercase">Hyperparameter Review (Human-in-Loop)</span>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] font-mono text-[var(--text-muted)]">Learning Rate</label>
                  <input 
                    type="text" 
                    value={customParams.learning_rate} 
                    onChange={(e) => setCustomParams({...customParams, learning_rate: e.target.value})}
                    className="bg-[var(--bg-card)] border app-border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] font-mono text-[var(--text-muted)]">Batch Size</label>
                  <input 
                    type="text" 
                    value={customParams.batch_size} 
                    onChange={(e) => setCustomParams({...customParams, batch_size: e.target.value})}
                    className="bg-[var(--bg-card)] border app-border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] font-mono text-[var(--text-muted)]">Optimizer</label>
                  <input 
                    type="text" 
                    value={customParams.optimizer} 
                    onChange={(e) => setCustomParams({...customParams, optimizer: e.target.value})}
                    className="bg-[var(--bg-card)] border app-border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] font-mono text-[var(--text-muted)]">Loss Function</label>
                  <input 
                    type="text" 
                    value={customParams.loss} 
                    onChange={(e) => setCustomParams({...customParams, loss: e.target.value})}
                    className="bg-[var(--bg-card)] border app-border rounded px-2 py-1 text-[var(--text-main)] font-mono text-[9px] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                approveParameters(customParams);
                sendMessage("Generate complete PyTorch model implementation code for this paper.", true);
                setActiveView('chat');
              }}
              className="mt-1 text-[10px] font-mono font-bold bg-[var(--accent)] hover:opacity-90 text-white px-5 py-2 rounded-xl transition-all shadow-lg active:scale-95 cursor-pointer"
            >
              Get Code in Chat
            </button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-3">
            <div className="flex gap-2 border-b app-border pb-1.5">
              <button
                onClick={() => setActiveTab('walkthrough')}
                className={`text-[9px] font-mono font-bold px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  activeTab === 'walkthrough' ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]' : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                }`}
              >
                Verification Walkthrough
              </button>
              <button
                onClick={() => setActiveTab('checklist')}
                className={`text-[9px] font-mono font-bold px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  activeTab === 'checklist' ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]' : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                }`}
              >
                Task Checklist
              </button>
            </div>

            <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[300px] flex flex-col gap-3">
              {isLoadingFiles ? (
                <div className="flex-1 flex items-center justify-center py-6">
                  <div className="w-5 h-5 rounded-full border border-[var(--accent)] border-t-transparent animate-spin"></div>
                </div>
              ) : activeTab === 'walkthrough' ? (
                <div className="text-[10px] text-[var(--text-main)] leading-relaxed font-mono whitespace-pre-wrap select-text selection:bg-[var(--accent-subtle)] p-1 rounded">
                  {parseMarkdown(walkthroughContent)}
                </div>
              ) : (
                <div className="text-[10px] text-[var(--text-main)] leading-relaxed font-mono whitespace-pre-wrap select-text selection:bg-[var(--accent-subtle)] p-1 rounded">
                  {parseMarkdown(taskContent)}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Slice report content for Brief tier view
  let displayMarkdown = reportContent;
  if (selectedTier === 'brief') {
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

  // Simple, robust Markdown parser helper to avoid installing excess NPM libraries
  function parseMarkdown(markdown: string) {
    const lines = markdown.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      
      // H1 Header
      if (trimmed.startsWith('# ')) {
        return <h1 key={idx} className="text-sm font-serif font-extrabold text-brass border-b border-parchment/10 pb-1 mt-4 mb-2">{trimmed.slice(2)}</h1>;
      }
      
      // H2 Header
      if (trimmed.startsWith('## ')) {
        return <h2 key={idx} className="text-xs font-serif font-bold text-parchment mt-3 mb-1.5">{trimmed.slice(3)}</h2>;
      }
      
      // Bullet list items
      if (trimmed.startsWith('* ')) {
        return (
          <ul key={idx} className="list-disc list-inside pl-2 text-[9.5px] text-foreground/80 leading-relaxed my-0.5">
            <li>{trimmed.slice(2)}</li>
          </ul>
        );
      }
      
      // Ignore raw markdown code block tags
      if (trimmed.startsWith('```')) {
        return null;
      }
      
      // Check for code configurations to format
      if (trimmed.includes(':') && !trimmed.startsWith('http')) {
        const parts = trimmed.split(':');
        return (
          <div key={idx} className="font-mono text-[8.5px] bg-black/20 px-2.5 py-0.5 border-l-2 border-brass/50 my-0.5 text-foreground/70">
            <strong>{parts[0]}:</strong>{parts.slice(1).join(':')}
          </div>
        );
      }
      
      // Blank spacing
      if (trimmed === '') return <div key={idx} className="h-1.5" />;
      
      // Regular text paragraphs
      return <p key={idx} className="text-[9.5px] text-foreground/80 leading-relaxed my-1">{trimmed}</p>;
    }).filter(Boolean);
  }

  return (
    <div className="bg-card/80 border border-border rounded-xl p-4 flex flex-col gap-3">
      <div className="flex flex-col gap-2.5 border-b border-border pb-3">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-mono font-bold text-brass uppercase tracking-wider">PROJECT PROPOSAL</span>
          <button 
            onClick={resetAnalysis} 
            className="text-[8px] font-mono font-bold bg-brass/10 hover:bg-brass hover:text-ink text-brass border border-brass/25 px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
          >
            Reset Analysis
          </button>
        </div>
        <TierSelector />
      </div>

      <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[300px]">
        {parseMarkdown(displayMarkdown)}
      </div>
    </div>
  );
};
